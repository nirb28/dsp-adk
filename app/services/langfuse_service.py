"""Langfuse v3 observability integration.

This is intentionally optional and becomes a no-op when disabled or when the
langfuse package is not installed.
"""

import logging
import json
from typing import Optional, Dict, Any

from ..config import get_settings
from ..models.telemetry import AgentAction, Trace, SpanStatus, ActionType

logger = logging.getLogger(__name__)


class LangfuseService:
    """Thin wrapper around the Langfuse Python SDK (v3)."""

    def __init__(self):
        self.settings = get_settings()
        self._enabled = bool(getattr(self.settings, "langfuse_enabled", False))
        self._client = None

        # Root observation per trace_id
        self._trace_roots: Dict[str, Any] = {}
        self._trace_root_ids: Dict[str, str] = {}
        self._trace_io: Dict[str, Dict[str, Any]] = {}
        # Observation per telemetry span_id
        self._span_observations: Dict[str, Any] = {}
        # Langfuse/OTEL span id per telemetry span_id
        self._span_ids: Dict[str, str] = {}

        if self._enabled:
            self._initialize()

    def _sanitize(self, value: Any) -> Any:
        """Best-effort conversion to JSON-serializable content.

        Langfuse input/output expects JSON-serializable objects. If we pass non-serializable
        types, payloads can be dropped.
        """
        if value is None:
            return None

        try:
            return json.loads(json.dumps(value, default=str))
        except Exception:
            try:
                return str(value)
            except Exception:
                return None

    def _initialize(self) -> None:
        try:
            from langfuse import Langfuse, get_client

            public_key = getattr(self.settings, "langfuse_public_key", None)
            secret_key = getattr(self.settings, "langfuse_secret_key", None)
            base_url = getattr(self.settings, "langfuse_base_url", None) or getattr(
                self.settings, "langfuse_host", None
            )

            # Prefer explicit constructor if keys are configured; else rely on env vars via get_client()
            if public_key and secret_key:
                kwargs: Dict[str, Any] = {
                    "public_key": public_key,
                    "secret_key": secret_key,
                }
                if base_url:
                    kwargs["base_url"] = base_url

                tracing_enabled = getattr(self.settings, "langfuse_tracing_enabled", None)
                if tracing_enabled is not None:
                    kwargs["tracing_enabled"] = tracing_enabled

                self._client = Langfuse(**kwargs)
            else:
                self._client = get_client()

            # Best-effort auth check
            try:
                if hasattr(self._client, "auth_check") and not self._client.auth_check():
                    logger.warning("Langfuse auth_check() failed; disabling Langfuse")
                    self._enabled = False
                    self._client = None
                    return
            except Exception:
                # Don't hard-fail if auth_check isn't possible
                pass

            logger.info("Langfuse initialized")

        except ImportError:
            logger.warning("Langfuse enabled but package is not installed; disabling Langfuse")
            self._enabled = False
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}", exc_info=True)
            self._enabled = False
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _action_to_observation_type(self, action_type: ActionType) -> str:
        if action_type == ActionType.LLM_REQUEST:
            return "generation"
        if action_type == ActionType.TOOL_CALL:
            return "tool"
        if action_type == ActionType.AGENT_START or action_type == ActionType.AGENT_END:
            return "agent"
        return "span"

    def on_trace_started(self, trace: Trace) -> None:
        if not self.enabled:
            return

        try:
            # Ensure we have a root span for the trace so that all actions can be parented.
            root = self._client.start_observation(
                trace_context={"trace_id": trace.trace_id},
                name=trace.name,
                as_type="span",
                input=self._sanitize({
                    "trace_id": trace.trace_id,
                    "agent_id": trace.agent_id,
                    "graph_id": trace.graph_id,
                    "user_id": trace.user_id,
                    "session_id": trace.session_id,
                }),
                metadata={
                    "adk.trace_id": trace.trace_id,
                    "adk.agent_id": trace.agent_id,
                    "adk.graph_id": trace.graph_id,
                    "adk.user_id": trace.user_id,
                    "adk.session_id": trace.session_id,
                },
            )

            # Set trace-level attributes (best-effort)
            try:
                if hasattr(root, "update_trace"):
                    root.update_trace(
                        user_id=trace.user_id,
                        session_id=trace.session_id,
                        metadata={
                            "adk.trace_id": trace.trace_id,
                            "adk.agent_id": trace.agent_id,
                            "adk.graph_id": trace.graph_id,
                        },
                        tags=["adk"],
                        name=trace.name,
                    )
            except Exception:
                pass

            self._trace_roots[trace.trace_id] = root

            root_id = getattr(root, "id", None) or getattr(root, "span_id", None)
            if root_id:
                self._trace_root_ids[trace.trace_id] = root_id
        except Exception as e:
            logger.debug(f"Langfuse on_trace_started failed: {e}")

    def update_trace(self, trace_id: str, *, input: Any = None, output: Any = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return

        root = self._trace_roots.get(trace_id)
        if root is None:
            return

        try:
            current = self._trace_io.get(trace_id, {})
            if input is not None:
                current["input"] = self._sanitize(input)
            if output is not None:
                current["output"] = self._sanitize(output)
            self._trace_io[trace_id] = current
        except Exception:
            pass

        try:
            if hasattr(root, "update_trace"):
                root.update_trace(
                    input=self._sanitize(input) if input is not None else None,
                    output=self._sanitize(output) if output is not None else None,
                    metadata=self._sanitize(metadata) if metadata is not None else None,
                )
        except Exception as e:
            logger.debug(f"Langfuse update_trace failed: {e}")

        # Also update the root observation itself so payloads are visible when inspecting the root span.
        try:
            if hasattr(root, "update"):
                update_kwargs: Dict[str, Any] = {}
                if input is not None:
                    update_kwargs["input"] = self._sanitize(input)
                if output is not None:
                    update_kwargs["output"] = self._sanitize(output)
                if metadata is not None:
                    update_kwargs["metadata"] = self._sanitize(metadata)
                if update_kwargs:
                    root.update(**update_kwargs)
        except Exception as e:
            logger.debug(f"Langfuse root.update failed: {e}")

    def on_trace_ended(self, trace_id: str, status: SpanStatus) -> None:
        if not self.enabled:
            return

        root = self._trace_roots.pop(trace_id, None)
        self._trace_root_ids.pop(trace_id, None)
        trace_io = self._trace_io.pop(trace_id, None)
        if root is None:
            return

        try:
            output = None
            if isinstance(trace_io, dict) and "output" in trace_io:
                output = trace_io.get("output")

            # In the installed Langfuse SDK, end() only closes the OTEL span and does not accept
            # output/level/etc. Apply final output via update() first, then end().
            try:
                if hasattr(root, "update"):
                    update_kwargs: Dict[str, Any] = {"output": self._sanitize(output)}
                    if status == SpanStatus.ERROR:
                        update_kwargs["level"] = "ERROR"
                    root.update(**update_kwargs)
            except Exception as e:
                logger.debug(f"Langfuse root.update failed: {e}")

            if hasattr(root, "end"):
                root.end()
        except Exception as e:
            logger.debug(f"Langfuse root end failed: {e}")

        try:
            if hasattr(self._client, "flush"):
                self._client.flush()
        except Exception:
            pass

    def on_action_started(self, action: AgentAction) -> None:
        if not self.enabled:
            return

        try:
            parent_langfuse_span_id = None
            if action.parent_span_id:
                parent_langfuse_span_id = self._span_ids.get(action.parent_span_id)
            if parent_langfuse_span_id is None:
                parent_langfuse_span_id = self._trace_root_ids.get(action.trace_id)

            obs_type = self._action_to_observation_type(action.action_type)
            metadata: Dict[str, Any] = {
                "adk.action_type": action.action_type.value,
                "adk.span_name": action.name,
                "adk.span_id": action.span_id,
                "adk.parent_span_id": action.parent_span_id,
                "adk.agent_id": action.agent_id,
                "adk.graph_id": action.graph_id,
                "adk.node_id": action.node_id,
                "adk.tool_id": action.tool_id,
                "adk.user_id": action.user_id,
                "adk.session_id": action.session_id,
            }
            if action.attributes:
                metadata.update({f"adk.attr.{k}": v for k, v in action.attributes.items()})

            # Langfuse requires JSON-serializable metadata; sanitize aggressively to avoid silent drops.
            metadata = self._sanitize(metadata) or {}

            # For generations, pass model fields if present
            model = None
            model_parameters = None
            if obs_type == "generation":
                model = action.attributes.get("model") if action.attributes else None
                if not model and action.attributes:
                    # Sometimes provider/model are split
                    provider = action.attributes.get("provider")
                    model_name = action.attributes.get("model")
                    if provider and model_name:
                        model = str(model_name)

                # Langfuse expects dict[str, MapValue]; passing plain values works in practice.
                model_parameters = {}
                if action.attributes:
                    for k in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
                        if k in action.attributes:
                            model_parameters[k] = action.attributes[k]

                model_parameters = self._sanitize(model_parameters) or None

            trace_context: Dict[str, Any] = {"trace_id": action.trace_id}
            if parent_langfuse_span_id:
                trace_context["parent_span_id"] = parent_langfuse_span_id

            obs = self._client.start_observation(
                trace_context=trace_context,
                name=action.name,
                as_type=obs_type,
                input=self._sanitize(action.input_data),
                metadata=metadata,
                model=model,
                model_parameters=model_parameters or None,
            )

            self._span_observations[action.span_id] = obs

            obs_id = getattr(obs, "id", None) or getattr(obs, "span_id", None)
            if obs_id:
                self._span_ids[action.span_id] = obs_id

        except Exception as e:
            logger.debug(f"Langfuse on_action_started failed: {e}")

    def on_action_completed(self, action: AgentAction) -> None:
        if not self.enabled:
            return

        obs = self._span_observations.pop(action.span_id, None)
        self._span_ids.pop(action.span_id, None)
        if obs is None:
            return

        try:
            is_generation = action.action_type == ActionType.LLM_REQUEST

            usage_details = None
            if is_generation and (
                action.token_count is not None or action.input_tokens is not None or action.output_tokens is not None
            ):
                usage_details = {
                    "total_tokens": action.token_count,
                    "prompt_tokens": action.input_tokens,
                    "completion_tokens": action.output_tokens,
                }

            # In the installed Langfuse SDK, end() only closes the OTEL span and does not accept
            # output/level/etc. Those must be applied via update() before end().
            try:
                if hasattr(obs, "update"):
                    update_kwargs: Dict[str, Any] = {
                        "output": self._sanitize(action.output_data),
                    }
                    if is_generation and usage_details is not None:
                        update_kwargs["usage_details"] = usage_details
                    if action.status == SpanStatus.ERROR:
                        update_kwargs["level"] = "ERROR"
                        if action.error_message:
                            update_kwargs["status_message"] = action.error_message
                    obs.update(**update_kwargs)
            except Exception as e:
                logger.debug(f"Langfuse obs.update failed: {e}")

            if hasattr(obs, "end"):
                obs.end()

        except Exception as e:
            logger.debug(f"Langfuse on_action_completed failed: {e}")

    def on_span_event(self, trace_id: str, span_id: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return

        parent_langfuse_span_id = self._span_ids.get(span_id) or self._trace_root_ids.get(trace_id)
        if parent_langfuse_span_id is None:
            return

        try:
            payload = self._sanitize(attributes or {})
            evt = self._client.start_observation(
                trace_context={"trace_id": trace_id, "parent_span_id": parent_langfuse_span_id},
                name=name,
                as_type="span",
                input=payload,
                output=payload,
                metadata=payload,
            )
            if hasattr(evt, "end"):
                evt.end()
        except Exception as e:
            logger.debug(f"Langfuse on_span_event failed: {e}")

    def flush(self) -> None:
        if not self.enabled:
            return

        try:
            if hasattr(self._client, "flush"):
                self._client.flush()
        except Exception:
            pass

    def shutdown(self) -> None:
        if not self.enabled:
            return

        try:
            if hasattr(self._client, "shutdown"):
                self._client.shutdown()
        except Exception:
            pass


_langfuse_service: Optional[LangfuseService] = None


def get_langfuse_service() -> LangfuseService:
    global _langfuse_service
    if _langfuse_service is None:
        _langfuse_service = LangfuseService()
    return _langfuse_service

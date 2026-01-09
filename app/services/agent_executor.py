"""
Agent Execution Service.

Handles the actual execution of agents including LLM calls, tool invocation,
memory management, and response generation.
"""
import os
import logging
import httpx
import json
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime

from ..models.agents import AgentConfig, LLMConfig
from ..models.tools import ToolConfig
from ..models.auth import AuthenticatedUser
from ..models.telemetry import ActionType, SpanStatus, SpanKind
from .tool_service import ToolService
from .skill_service import get_skill_service
from .telemetry_service import get_telemetry_service
from ..config import get_settings

logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Exception raised during agent execution."""
    pass


class LLMProvider:
    """Base class for LLM provider integrations."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key
        if not self.api_key:
            logger.warning(f"[AGENT_EXEC] No API key configured for provider '{self.config.provider}'")
        else:
            logger.debug(f"[AGENT_EXEC] API key loaded for provider '{self.config.provider}'")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        raise NotImplementedError
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, Groq, NVIDIA, etc.)."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.endpoint or "https://api.openai.com/v1"
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using OpenAI-compatible API."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        # Use max_completion_tokens if specified, otherwise fall back to max_tokens
        if self.config.max_completion_tokens is not None:
            payload["max_completion_tokens"] = kwargs.get("max_completion_tokens", self.config.max_completion_tokens)
        elif self.config.max_tokens is not None:
            payload["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"  # Let LLM decide when to use tools
            payload["parallel_tool_calls"] = False  # Groq compatibility
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response using OpenAI-compatible API."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }
        
        # Use max_completion_tokens if specified, otherwise fall back to max_tokens
        if self.config.max_completion_tokens is not None:
            payload["max_completion_tokens"] = kwargs.get("max_completion_tokens", self.config.max_completion_tokens)
        elif self.config.max_tokens is not None:
            payload["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            payload["parallel_tool_calls"] = False  # Groq compatibility
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue


class AgentExecutor:
    """
    Service for executing agents.
    
    Handles:
    - LLM provider integration
    - Message formatting
    - Tool calling
    - Memory management
    - Response generation
    """
    
    def __init__(self):
        self.providers: Dict[str, type] = {
            "openai": OpenAIProvider,
            "groq": OpenAIProvider,
            "nvidia": OpenAIProvider,
            "anthropic": OpenAIProvider,
        }
        self.tool_service = ToolService()
        self.skill_service = get_skill_service()
        self.telemetry_service = get_telemetry_service()
        self.settings = get_settings()
        self.verbose_logging = self.settings.verbose_logging
    
    def _get_provider(self, config: LLMConfig) -> LLMProvider:
        """Get the appropriate LLM provider."""
        provider_class = self.providers.get(config.provider.lower())
        if not provider_class:
            raise AgentExecutionError(f"Unsupported LLM provider: {config.provider}")
        return provider_class(config)
    
    def _build_messages(
        self,
        agent: AgentConfig,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build the messages array for the LLM with skill integration."""
        messages = []
        
        # Get base system prompt
        system_prompt = agent.llm.system_prompt
        if not system_prompt and hasattr(agent, 'system_prompt'):
            system_prompt = getattr(agent, 'system_prompt', None)
        
        # Apply skills if configured
        if hasattr(agent, 'skills') and agent.skills:
            logger.debug(f"[AGENT_EXEC] Applying {len(agent.skills)} skills to agent")
            system_prompt, messages = self.skill_service.load_and_apply_skills(
                skill_instances=agent.skills,
                system_prompt=system_prompt or "",
                messages=messages,
                trace_id=trace_id,
                parent_span_id=parent_span_id
            )
        
        # Add final system prompt if we have one
        if system_prompt:
            # Check if skills already added system messages
            has_system = any(msg.get("role") == "system" for msg in messages)
            if has_system:
                # Update the first system message with combined prompt
                for msg in messages:
                    if msg.get("role") == "system":
                        msg["content"] = system_prompt
                        break
            else:
                # Add new system message
                messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append({
                "role": "system",
                "content": f"Context:\n{context_str}"
            })
        
        # Add conversation history
        if history:
            messages.extend(history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _load_agent_tools(self, agent: AgentConfig) -> List[ToolConfig]:
        """Load tool configurations for an agent."""
        tools = []
        if not hasattr(agent, 'tools') or not agent.tools:
            return tools
        
        for tool_id in agent.tools:
            tool = self.tool_service.get_tool(tool_id)
            if tool and tool.enabled:
                tools.append(tool)
            else:
                logger.warning(f"Tool '{tool_id}' not found or disabled")
        
        return tools
    
    def _convert_tool_to_openai_function(self, tool: ToolConfig) -> Dict[str, Any]:
        """Convert a ToolConfig to OpenAI function calling format."""
        properties = {}
        required = []
        
        for param in tool.parameters:
            param_schema = {
                "type": param.type,
            }
            if param.description:
                param_schema["description"] = param.description
            if param.enum:
                param_schema["enum"] = param.enum
            
            properties[param.name] = param_schema
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": tool.id,
                "description": tool.description or tool.name,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def _get_mock_response(self, tool: ToolConfig, arguments: Dict[str, Any]) -> str:
        """Generate mock response for a tool."""
        if tool.id == "web-search":
            query = arguments.get("query", "")
            num_results = arguments.get("num_results", 5)
            return json.dumps({
                "results": [
                    {
                        "title": f"Result {i+1} for: {query}",
                        "url": f"https://example.com/result{i+1}",
                        "snippet": f"This is a snippet about {query}..."
                    }
                    for i in range(num_results)
                ]
            })
        elif tool.id == "text-processor":
            text = arguments.get("text", "")
            operation = arguments.get("operation", "summarize")
            return json.dumps({
                "result": f"Processed text with {operation}: {text[:100]}...",
                "operation": operation
            })
        else:
            return json.dumps({"result": "Tool executed successfully (mock)"})
    
    def _substitute_template_vars(self, template: str, arguments: Dict[str, Any], tool: Optional[ToolConfig] = None) -> str:
        """Substitute {{variable}} placeholders in template strings."""
        import re
        
        result = template
        
        # First pass: substitute provided arguments
        for key, value in arguments.items():
            placeholder = f"{{{{{key}}}}}"
            # Handle JSON serialization for complex types
            if value is None:
                result = result.replace(placeholder, "null")
            elif isinstance(value, bool):
                result = result.replace(placeholder, "true" if value else "false")
            elif isinstance(value, (dict, list)):
                result = result.replace(placeholder, json.dumps(value))
            elif isinstance(value, str):
                # Don't quote strings - let the template handle quoting
                result = result.replace(placeholder, value)
            else:
                result = result.replace(placeholder, str(value))
        
        # Second pass: handle remaining placeholders with defaults from tool parameters
        if tool:
            remaining_placeholders = re.findall(r'\{\{(\w+)\}\}', result)
            for param_name in remaining_placeholders:
                # Find parameter definition in tool config
                param_def = next((p for p in tool.parameters if p.name == param_name), None)
                if param_def and param_def.default is not None:
                    placeholder = f"{{{{{param_name}}}}}"
                    default_value = param_def.default
                    if default_value is None:
                        result = result.replace(placeholder, "null")
                    elif isinstance(default_value, bool):
                        result = result.replace(placeholder, "true" if default_value else "false")
                    elif isinstance(default_value, (dict, list)):
                        result = result.replace(placeholder, json.dumps(default_value))
                    elif isinstance(default_value, str):
                        result = result.replace(placeholder, default_value)
                    else:
                        result = result.replace(placeholder, str(default_value))
        
        return result
    
    async def _execute_api_tool(self, tool: ToolConfig, arguments: Dict[str, Any]) -> str:
        """Execute an API tool by making HTTP request."""
        impl = tool.implementation
        
        # Get endpoint and method
        endpoint = impl.get("endpoint", "")
        method = impl.get("method", "GET").upper()
        
        logger.debug(f"[TOOL_EXEC:API] Tool '{tool.id}': endpoint_template={endpoint}, method={method}")
        
        if not endpoint:
            return json.dumps({"error": "No endpoint configured for API tool"})
        
        # Substitute template variables in endpoint
        endpoint = self._substitute_template_vars(endpoint, arguments, tool)
        logger.debug(f"[TOOL_EXEC:API] Resolved endpoint: {endpoint}")
        
        # Build headers
        headers = {}
        if "headers" in impl:
            for key, value in impl["headers"].items():
                headers[key] = self._substitute_template_vars(str(value), arguments, tool)
        
        # Build query parameters
        params = {}
        if "query_params" in impl:
            for key, value in impl["query_params"].items():
                params[key] = self._substitute_template_vars(str(value), arguments, tool)
        
        # Build request body
        body = None
        # Check for both "body" and "body_template" keys
        body_source = impl.get("body_template") or impl.get("body")
        if body_source:
            if isinstance(body_source, dict):
                body = {}
                for key, value in body_source.items():
                    body[key] = self._substitute_template_vars(str(value), arguments, tool)
            elif isinstance(body_source, str):
                # Handle string templates - substitute vars then parse as JSON
                body_str = self._substitute_template_vars(body_source, arguments, tool)
                
                # Remove lines with unsubstituted placeholders (optional parameters not provided)
                import re
                lines = body_str.split('\n')
                filtered_lines = []
                for line in lines:
                    # Check if line contains unsubstituted placeholder
                    if re.search(r'\{\{[^}]+\}\}', line):
                        # Skip this line - it has an unsubstituted placeholder
                        continue
                    filtered_lines.append(line)
                
                # Rejoin and clean up trailing commas before closing braces/brackets
                body_str = '\n'.join(filtered_lines)
                body_str = re.sub(r',(\s*[}\]])', r'\1', body_str)
                
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError as e:
                    logger.error(f"[TOOL_EXEC:API] Failed to parse body_template as JSON: {e}")
                    logger.debug(f"[TOOL_EXEC:API] Body string was: {body_str}")
                    return json.dumps({"error": f"Invalid JSON in body_template: {str(e)}"})
            else:
                body = self._substitute_template_vars(str(body_source), arguments, tool)
        
        # Make HTTP request
        timeout = tool.timeout or 30
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                logger.info(f"[TOOL_EXEC:API] Making request: {method} {endpoint}")
                logger.debug(f"[TOOL_EXEC:API] Headers: {json.dumps(headers, indent=2)}")
                logger.debug(f"[TOOL_EXEC:API] Params: {json.dumps(params, indent=2)}")
                if body:
                    logger.debug(f"[TOOL_EXEC:API] Body: {json.dumps(body, indent=2)}")
                
                if method == "GET":
                    response = await client.get(endpoint, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(endpoint, headers=headers, params=params, json=body)
                elif method == "PUT":
                    response = await client.put(endpoint, headers=headers, params=params, json=body)
                elif method == "DELETE":
                    response = await client.delete(endpoint, headers=headers, params=params)
                else:
                    return json.dumps({"error": f"Unsupported HTTP method: {method}"})
                
                response.raise_for_status()
                logger.debug(f"[TOOL_EXEC:API] Response status: {response.status_code}")
                
                # Try to parse as JSON, fallback to text
                try:
                    result = response.json()
                    logger.debug(f"[TOOL_EXEC:API] Response JSON keys: {list(result.keys()) if isinstance(result, dict) else 'array'}")
                    return json.dumps(result)
                except:
                    logger.debug(f"[TOOL_EXEC:API] Response as text, length: {len(response.text)}")
                    return json.dumps({"result": response.text})
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"API tool '{tool.id}' HTTP error: {e}")
                return json.dumps({
                    "error": f"HTTP {e.response.status_code}: {e.response.text}"
                })
            except Exception as e:
                logger.error(f"API tool '{tool.id}' error: {e}")
                return json.dumps({"error": str(e)})
    
    async def _execute_python_tool(self, tool: ToolConfig, arguments: Dict[str, Any]) -> str:
        """Execute a Python tool by calling a function."""
        impl = tool.implementation
        
        module_name = impl.get("module")
        function_name = impl.get("function")
        
        logger.debug(f"[TOOL_EXEC:PYTHON] Tool '{tool.id}': module={module_name}, function_template={function_name}")
        
        if not module_name or not function_name:
            return json.dumps({"error": "Python tool missing module or function"})
        
        # Substitute template variables in function name (e.g., {{operation}}_text)
        original_function_template = function_name
        function_name = self._substitute_template_vars(function_name, arguments)
        logger.debug(f"[TOOL_EXEC:PYTHON] Resolved function name: {function_name}")
        
        # Filter out template variables from arguments before calling function
        # Extract template variable names from the function template
        import re
        template_vars = set(re.findall(r'\{\{(\w+)\}\}', original_function_template))
        function_args = {k: v for k, v in arguments.items() if k not in template_vars}
        logger.debug(f"[TOOL_EXEC:PYTHON] Template vars filtered: {template_vars}")
        logger.debug(f"[TOOL_EXEC:PYTHON] Function args: {json.dumps(function_args, indent=2)}")
        
        try:
            # Dynamic import
            import importlib
            import inspect
            logger.debug(f"[TOOL_EXEC:PYTHON] Importing module: {module_name}")
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            
            # Add tool_config to function arguments so tools can access their configuration
            function_args['tool_config'] = tool.model_dump()
            
            # Call function with filtered arguments
            logger.info(f"[TOOL_EXEC:PYTHON] Calling: {module_name}.{function_name}")
            result = func(**function_args)
            
            # Check if result is a coroutine and await it
            if inspect.iscoroutine(result):
                logger.debug(f"[TOOL_EXEC:PYTHON] Function returned coroutine, awaiting...")
                result = await result
            
            # Convert result to JSON string
            if isinstance(result, str):
                return result
            else:
                return json.dumps(result)
                
        except ImportError as e:
            logger.error(f"Python tool '{tool.id}' import error: {e}")
            return json.dumps({"error": f"Failed to import {module_name}: {str(e)}"})
        except AttributeError as e:
            logger.error(f"Python tool '{tool.id}' function not found: {e}")
            return json.dumps({"error": f"Function {function_name} not found in {module_name}"})
        except Exception as e:
            logger.error(f"Python tool '{tool.id}' execution error: {e}")
            return json.dumps({"error": str(e)})
    
    async def _execute_shell_tool(self, tool: ToolConfig, arguments: Dict[str, Any]) -> str:
        """Execute a shell command tool."""
        impl = tool.implementation
        
        command = impl.get("command")
        logger.debug(f"[TOOL_EXEC:SHELL] Tool '{tool.id}': command_template={command}")
        
        if not command:
            return json.dumps({"error": "Shell tool missing command"})
        
        # Substitute arguments in command
        command = self._substitute_template_vars(command, arguments)
        logger.debug(f"[TOOL_EXEC:SHELL] Resolved command: {command}")
        
        try:
            import subprocess
            logger.info(f"[TOOL_EXEC:SHELL] Executing: {command}")
            
            timeout = tool.timeout or 30
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return json.dumps({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                })
            else:
                return json.dumps({
                    "error": f"Command failed with code {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"Command timed out after {timeout}s"})
        except Exception as e:
            logger.error(f"Shell tool '{tool.id}' error: {e}")
            return json.dumps({"error": str(e)})
    
    async def _execute_mcp_tool(self, tool: ToolConfig, arguments: Dict[str, Any]) -> str:
        """Execute an MCP (Model Context Protocol) tool."""
        impl = tool.implementation
        
        mcp_server_id = impl.get("mcp_server_id")
        tool_name = impl.get("tool_name")
        
        if not mcp_server_id or not tool_name:
            return json.dumps({"error": "MCP tool missing server_id or tool_name"})
        
        # TODO: Implement MCP client integration
        # For now, return placeholder
        logger.warning(f"MCP tool execution not yet implemented: {tool.id}")
        return json.dumps({
            "error": "MCP tool execution not yet implemented",
            "mcp_server_id": mcp_server_id,
            "tool_name": tool_name
        })
    
    async def _execute_tool(self, tool: ToolConfig, arguments: Dict[str, Any], mock: bool = False, trace_id: Optional[str] = None, parent_span_id: Optional[str] = None) -> str:
        """Execute a tool with given arguments."""
        span = None
        try:
            logger.info(f"[TOOL_EXEC] Starting execution: tool_id='{tool.id}', type={tool.tool_type}, mock={mock}")
            if self.verbose_logging:
                logger.info(f"[TOOL_EXEC:VERBOSE] Tool '{tool.id}' full arguments payload: {json.dumps(arguments, indent=2)}")
            else:
                logger.debug(f"[TOOL_EXEC] Tool '{tool.id}' arguments: {json.dumps(arguments, indent=2)}")
            
            # Start telemetry span for tool execution
            if trace_id:
                span = self.telemetry_service.log_action(
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    action_type=ActionType.TOOL_CALL,
                    name=f"tool_{tool.id}",
                    tool_id=tool.id,
                    input_data={"arguments": arguments, "mock": mock},
                    attributes={"tool_type": tool.tool_type, "tool_name": tool.name},
                    kind=SpanKind.INTERNAL
                )
            
            # Use mock response if requested
            if mock:
                logger.debug(f"[TOOL_EXEC] Using mock response for '{tool.id}'")
                result = self._get_mock_response(tool, arguments)
                logger.debug(f"[TOOL_EXEC] Mock result: {result[:200]}...")
                return result
            
            # Route to appropriate executor based on tool type
            logger.debug(f"[TOOL_EXEC] Routing to {tool.tool_type} executor for '{tool.id}'")
            if tool.tool_type == "api":
                result = await self._execute_api_tool(tool, arguments)
            elif tool.tool_type == "python":
                result = await self._execute_python_tool(tool, arguments)
            elif tool.tool_type == "shell":
                result = await self._execute_shell_tool(tool, arguments)
            elif tool.tool_type == "mcp":
                result = await self._execute_mcp_tool(tool, arguments)
            else:
                # Fallback to mock for unknown types
                logger.warning(f"[TOOL_EXEC] Unknown tool type '{tool.tool_type}', using mock response")
                result = self._get_mock_response(tool, arguments)
            
            logger.info(f"[TOOL_EXEC] Completed: tool_id='{tool.id}', result_length={len(result)}")
            if self.verbose_logging:
                logger.info(f"[TOOL_EXEC:VERBOSE] Tool '{tool.id}' full result payload: {result}")
            else:
                logger.debug(f"[TOOL_EXEC] Result preview: {result[:200]}...")
            
            # Complete telemetry span
            if span:
                # Add tool result as span event for detailed inspection
                self.telemetry_service.add_span_event(
                    span_id=span.span_id,
                    name="tool_result_payload",
                    attributes={
                        "result_preview": result[:1000] if len(result) <= 1000 else result[:1000] + "...",
                        "result_length": len(result),
                        "tool_type": tool.tool_type
                    }
                )
                
                self.telemetry_service.complete_action(
                    span_id=span.span_id,
                    status=SpanStatus.OK,
                    output_data={"result_length": len(result)}
                )
            
            return result
                
        except Exception as e:
            logger.error(f"[TOOL_EXEC] Error executing tool '{tool.id}': {e}", exc_info=True)
            
            # Mark span as error
            if span:
                self.telemetry_service.complete_action(
                    span_id=span.span_id,
                    status=SpanStatus.ERROR,
                    error_message=str(e)
                )
            
            return json.dumps({"error": str(e)})
    
    async def run(
        self,
        agent: AgentConfig,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user: Optional[AuthenticatedUser] = None,
        use_tools: bool = True,
        max_tool_iterations: int = 5,
        mock_tools: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an agent with a message.
        
        Args:
            agent: Agent configuration
            message: User message
            context: Optional context dictionary
            history: Optional conversation history
            user: Optional authenticated user
            use_tools: Whether to enable tool calling
            max_tool_iterations: Maximum number of tool calling iterations
            mock_tools: Use mock responses instead of real tool execution
            **kwargs: Additional parameters for LLM
            
        Returns:
            Dict with response, usage, and metadata
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"[AGENT_EXEC] Starting agent execution: agent_id='{agent.id}', agent_name='{agent.name}'")
            logger.debug(f"[AGENT_EXEC] Message: {message[:100]}...")
            logger.debug(f"[AGENT_EXEC] Context: {context}")
            logger.debug(f"[AGENT_EXEC] use_tools={use_tools}, mock_tools={mock_tools}, max_iterations={max_tool_iterations}")
            
            # Start telemetry trace
            trace = self.telemetry_service.start_trace(
                name=f"agent_execution_{agent.id}",
                agent_id=agent.id,
                user_id=user.user_id if user else None,
                session_id=kwargs.get('session_id')
            )
            trace_id = trace.trace_id

            # Store trace-level input for Langfuse (best-effort)
            try:
                if hasattr(self.telemetry_service, 'langfuse_service') and self.telemetry_service.langfuse_service.enabled:
                    self.telemetry_service.langfuse_service.update_trace(
                        trace_id,
                        input={
                            "message": message,
                            "context": context,
                            "history": history,
                            "use_tools": use_tools,
                            "max_tool_iterations": max_tool_iterations,
                            "mock_tools": mock_tools,
                        }
                    )
            except Exception:
                pass
            
            # Log agent start action
            agent_span = self.telemetry_service.log_action(
                trace_id=trace_id,
                action_type=ActionType.AGENT_START,
                name=f"agent_{agent.id}_start",
                agent_id=agent.id,
                user_id=user.user_id if user else None,
                input_data={"message": message[:200], "use_tools": use_tools},
                attributes={
                    "agent_name": agent.name,
                    "llm_provider": agent.llm.provider,
                    "llm_model": agent.llm.model
                },
                kind=SpanKind.SERVER
            )
            
            # Get LLM provider
            logger.debug(f"[AGENT_EXEC] Getting LLM provider: {agent.llm.provider}")
            provider = self._get_provider(agent.llm)
            logger.debug(f"[AGENT_EXEC] LLM provider initialized: {agent.llm.model}")
            
            # Build messages
            logger.debug(f"[AGENT_EXEC] Building messages array")
            messages = self._build_messages(
                agent,
                message,
                context,
                history,
                trace_id=trace_id,
                parent_span_id=agent_span.span_id if agent_span else None
            )
            logger.debug(f"[AGENT_EXEC] Built {len(messages)} messages")
            
            # Load and convert tools if enabled
            tools = None
            tool_configs = {}
            agent_tool_defaults = {}
            if use_tools and hasattr(agent, 'tools') and agent.tools:
                logger.debug(f"[AGENT_EXEC] Loading tools for agent: {agent.tools}")
                loaded_tools = self._load_agent_tools(agent)
                if loaded_tools:
                    tools = [self._convert_tool_to_openai_function(t) for t in loaded_tools]
                    tool_configs = {t.id: t for t in loaded_tools}
                    logger.info(f"[AGENT_EXEC] Loaded {len(tools)} tools: {list(tool_configs.keys())}")
                    
                    # Load agent's tool_configs (default parameters)
                    if hasattr(agent, 'tool_configs') and agent.tool_configs:
                        agent_tool_defaults = agent.tool_configs
                        logger.debug(f"[AGENT_EXEC] Agent tool defaults: {json.dumps(agent_tool_defaults, indent=2)}")
                else:
                    logger.warning(f"[AGENT_EXEC] No tools loaded for agent '{agent.id}'")
            else:
                logger.debug(f"[AGENT_EXEC] Tool calling disabled or no tools configured")

            if tools:
                try:
                    tool_lines = []
                    for tool_id, cfg in tool_configs.items():
                        param_names = [p.name for p in (cfg.parameters or [])]
                        required_names = [p.name for p in (cfg.parameters or []) if getattr(p, 'required', False)]
                        line = f"- {tool_id}: params={param_names}, required={required_names}"
                        if getattr(cfg, "usage_instructions", None):
                            line += f"\n  instructions: {cfg.usage_instructions}"
                        if getattr(cfg, "fallback_to_user_message_params", None):
                            line += f"\n  fallback_from_user_message: {cfg.fallback_to_user_message_params}"
                        tool_lines.append(line)
                    constraints = (
                        "Tool usage rules:\n"
                        "1) Only call tools using the exact parameter names listed below. Do not invent parameters.\n"
                        "2) Follow each tool's instructions (if provided).\n"
                        "3) After using tools, write a final plain-text answer with citations (URLs).\n\n"
                        "Available tools:\n" + "\n".join(tool_lines)
                    )

                    insert_at = len(messages)
                    if messages and messages[-1].get("role") == "user":
                        insert_at = len(messages) - 1
                    messages.insert(insert_at, {"role": "system", "content": constraints})
                except Exception:
                    pass
            
            # Execute with tool calling loop
            iteration = 0
            total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            total_tool_calls = 0
            
            while iteration < max_tool_iterations:
                iteration += 1
                logger.info(f"[AGENT_EXEC] === Iteration {iteration}/{max_tool_iterations} ===")
                logger.debug(f"[AGENT_EXEC] Calling LLM with {len(messages)} messages, {len(tools) if tools else 0} tools available")
                
                # Log LLM request
                llm_span = self.telemetry_service.log_action(
                    trace_id=trace_id,
                    parent_span_id=agent_span.span_id,
                    action_type=ActionType.LLM_REQUEST,
                    name=f"llm_call_iter_{iteration}",
                    agent_id=agent.id,
                    input_data={
                        "messages": messages,
                        "tools": tools,
                        "kwargs": kwargs,
                        "message_count": len(messages),
                        "tools_available": len(tools) if tools else 0,
                    },
                    attributes={
                        "provider": agent.llm.provider,
                        "model": agent.llm.model,
                        "iteration": iteration
                    },
                    kind=SpanKind.CLIENT
                )
                
                response = await provider.generate(messages, tools, **kwargs)
                logger.debug(f"[AGENT_EXEC] LLM response received")
                
                if self.verbose_logging:
                    logger.info(f"[AGENT_EXEC:VERBOSE] Full LLM request payload: {json.dumps({'messages': messages, 'tools': tools, 'kwargs': kwargs}, indent=2, default=str)}")
                    logger.info(f"[AGENT_EXEC:VERBOSE] Full LLM response payload: {json.dumps(response, indent=2, default=str)}")
                
                # Add LLM request/response as span events for detailed inspection
                if trace_id and llm_span:
                    # Add request event
                    self.telemetry_service.add_span_event(
                        span_id=llm_span.span_id,
                        name="llm_request_payload",
                        attributes={
                            "message_count": len(messages),
                            "last_message": messages[-1].get("content", "")[:2000] if messages else "",
                            "tools_count": len(tools) if tools else 0,
                            "tools_available": json.dumps([t.get("function", {}).get("name") for t in (tools or [])])
                        }
                    )
                    # Add response event
                    response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    response_message = response.get("choices", [{}])[0].get("message", {})
                    tool_calls_in_response = response_message.get("tool_calls", [])
                    
                    self.telemetry_service.add_span_event(
                        span_id=llm_span.span_id,
                        name="llm_response_payload",
                        attributes={
                            "content_preview": response_content[:2000] if response_content else "",
                            "content_length": len(response_content) if response_content else 0,
                            "finish_reason": response.get("choices", [{}])[0].get("finish_reason", ""),
                            "has_tool_calls": len(tool_calls_in_response) > 0,
                            "tool_calls_count": len(tool_calls_in_response),
                            "tool_calls_summary": json.dumps([
                                {
                                    "id": tc.get("id"),
                                    "function": tc.get("function", {}).get("name"),
                                    "args_preview": tc.get("function", {}).get("arguments", "")[:1000]
                                }
                                for tc in tool_calls_in_response
                            ]) if tool_calls_in_response else "[]"
                        }
                    )
                
                # Accumulate usage
                if "usage" in response:
                    for key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                        total_usage[key] += response["usage"].get(key, 0)
                    logger.debug(f"[AGENT_EXEC] Token usage this iteration: {response['usage']}")
                    
                    # Complete LLM span with token usage
                    self.telemetry_service.complete_action(
                        span_id=llm_span.span_id,
                        status=SpanStatus.OK,
                        output_data={
                            "response": response,
                            "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
                        },
                        token_count=response["usage"].get("total_tokens", 0)
                    )
                else:
                    # Complete without token info
                    self.telemetry_service.complete_action(
                        span_id=llm_span.span_id,
                        status=SpanStatus.OK,
                        output_data={"response": response}
                    )
                
                # Check if LLM wants to call tools
                if "choices" not in response or len(response["choices"]) == 0:
                    logger.debug(f"[AGENT_EXEC] No choices in response, ending loop")
                    break
                
                choice = response["choices"][0]
                finish_reason = choice.get("finish_reason")
                logger.debug(f"[AGENT_EXEC] Finish reason: {finish_reason}")
                
                # If no tool calls, we're done
                if finish_reason != "tool_calls":
                    logger.debug(f"[AGENT_EXEC] No tool calls requested, ending loop")
                    break
                
                # Process tool calls
                tool_calls = choice.get("message", {}).get("tool_calls", [])
                if not tool_calls:
                    logger.debug(f"[AGENT_EXEC] Empty tool_calls array, ending loop")
                    break
                
                logger.info(f"[AGENT_EXEC] Processing {len(tool_calls)} tool call(s)")
                total_tool_calls += len(tool_calls)
                
                # Log tool calls detection as span event
                if trace_id and llm_span:
                    self.telemetry_service.add_span_event(
                        span_id=llm_span.span_id,
                        name="tool_calls_detected",
                        attributes={
                            "tool_calls_count": len(tool_calls),
                            "tool_names": json.dumps([tc.get("function", {}).get("name") for tc in tool_calls]),
                            "iteration": iteration
                        }
                    )
                
                # Add assistant message with tool calls to conversation
                messages.append(choice["message"])
                
                # Execute each tool call
                for idx, tool_call in enumerate(tool_calls, 1):
                    tool_id = tool_call["function"]["name"]
                    raw_args = tool_call["function"].get("arguments")
                    if isinstance(raw_args, dict):
                        tool_args = raw_args
                    else:
                        tool_args = json.loads(raw_args) if raw_args else {}
                    logger.info(f"[AGENT_EXEC] Tool call {idx}/{len(tool_calls)}: {tool_id}")
                    logger.debug(f"[AGENT_EXEC] Tool call ID: {tool_call['id']}")
                    logger.debug(f"[AGENT_EXEC] LLM-provided arguments: {json.dumps(tool_args, indent=2)}")
                    
                    # Merge agent's default tool configs with LLM's arguments
                    # Agent defaults take precedence over LLM arguments
                    if tool_id in agent_tool_defaults:
                        merged_args = {**tool_args, **agent_tool_defaults[tool_id]}
                        logger.debug(f"[AGENT_EXEC] Merged with agent defaults: {json.dumps(merged_args, indent=2)}")
                        tool_args = merged_args

                    if tool_id in tool_configs:
                        try:
                            required_params = [
                                p.name for p in (tool_configs[tool_id].parameters or [])
                                if getattr(p, 'required', False)
                            ]
                            missing = [p for p in required_params if p not in tool_args or tool_args.get(p) in (None, "")]
                            if missing:
                                fallback_params = getattr(tool_configs[tool_id], "fallback_to_user_message_params", None) or []
                                for p in list(missing):
                                    if p in fallback_params:
                                        tool_args[p] = message
                                        missing = [mp for mp in missing if mp != p]

                            if missing:
                                result = json.dumps({
                                    "error": f"Missing required parameter(s) for tool '{tool_id}': {missing}",
                                    "provided_args": tool_args
                                })
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": result
                                })
                                continue
                        except Exception:
                            pass

                        result = await self._execute_tool(
                            tool_configs[tool_id], 
                            tool_args, 
                            mock=mock_tools,
                            trace_id=trace_id,
                            parent_span_id=agent_span.span_id
                        )
                    else:
                        logger.error(f"[AGENT_EXEC] Tool '{tool_id}' not found in loaded tools")
                        result = json.dumps({"error": f"Tool '{tool_id}' not found"})
                    
                    # Add tool response to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
                    logger.debug(f"[AGENT_EXEC] Tool result added to conversation (length: {len(result)} chars)")
                
                # Continue loop to get final response
            
            # Extract final response
            logger.debug(f"[AGENT_EXEC] Tool calling loop completed after {iteration} iterations")
            if iteration >= max_tool_iterations:
                messages.append({
                    "role": "system",
                    "content": "Stop using tools now. Provide the final answer in plain text with citations (URLs) based on the tool results above."
                })
                response = await provider.generate(messages, None, **kwargs)
            else:
                response = response
            
            # Extract response content
            content = ""
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"[AGENT_EXEC] Execution completed successfully")
            logger.debug(f"[AGENT_EXEC] Duration: {duration:.2f}s, Tool calls: {total_tool_calls if use_tools else 0}")
            logger.debug(f"[AGENT_EXEC] Total tokens: {total_usage.get('total_tokens', 0)}")
            logger.debug(f"[AGENT_EXEC] Response length: {len(content)} characters")
            
            # Complete agent span
            self.telemetry_service.complete_action(
                span_id=agent_span.span_id,
                status=SpanStatus.OK,
                output_data={"response_length": len(content), "tool_calls": total_tool_calls if use_tools else 0},
                token_count=total_usage.get('total_tokens', 0)
            )

            # Store trace-level output for Langfuse (best-effort)
            try:
                if hasattr(self.telemetry_service, 'langfuse_service') and self.telemetry_service.langfuse_service.enabled:
                    self.telemetry_service.langfuse_service.update_trace(
                        trace_id,
                        output={
                            "response": content,
                            "usage": total_usage if use_tools else response.get("usage", {}),
                            "model": agent.llm.model,
                            "provider": agent.llm.provider,
                            "duration_seconds": duration,
                            "tool_calls_made": total_tool_calls if use_tools else 0,
                        }
                    )
            except Exception:
                pass
            
            # End trace
            self.telemetry_service.end_trace(trace_id, SpanStatus.OK)
            
            return {
                "success": True,
                "response": content,
                "usage": total_usage if use_tools else response.get("usage", {}),
                "model": agent.llm.model,
                "provider": agent.llm.provider,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
                "agent_id": agent.id,
                "agent_name": agent.name,
                "tool_calls_made": total_tool_calls if use_tools else 0,
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing agent: {e}")
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            
            # Mark trace as error if it exists
            if 'trace_id' in locals():
                self.telemetry_service.end_trace(trace_id, SpanStatus.ERROR)
            
            raise AgentExecutionError(f"LLM API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error executing agent: {e}", exc_info=True)
            
            # Mark trace as error if it exists
            if 'trace_id' in locals():
                self.telemetry_service.end_trace(trace_id, SpanStatus.ERROR)
            
            raise AgentExecutionError(f"Execution failed: {str(e)}")
    
    async def stream(
        self,
        agent: AgentConfig,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user: Optional[AuthenticatedUser] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Execute an agent with streaming response.
        
        Args:
            agent: Agent configuration
            message: User message
            context: Optional context dictionary
            history: Optional conversation history
            user: Optional authenticated user
            **kwargs: Additional parameters for LLM
            
        Yields:
            Response chunks as they arrive
        """
        try:
            start_time = datetime.utcnow()

            trace = self.telemetry_service.start_trace(
                name=f"agent_stream_{agent.id}",
                agent_id=agent.id,
                user_id=user.user_id if user else None,
                session_id=kwargs.get('session_id')
            )
            trace_id = trace.trace_id

            # Store trace-level input for Langfuse (best-effort)
            try:
                if hasattr(self.telemetry_service, 'langfuse_service') and self.telemetry_service.langfuse_service.enabled:
                    self.telemetry_service.langfuse_service.update_trace(
                        trace_id,
                        input={
                            "message": message,
                            "context": context,
                            "history": history,
                            "stream": True,
                        }
                    )
            except Exception:
                pass

            agent_span = self.telemetry_service.log_action(
                trace_id=trace_id,
                action_type=ActionType.AGENT_START,
                name=f"agent_{agent.id}_stream_start",
                agent_id=agent.id,
                user_id=user.user_id if user else None,
                input_data={"message": message[:200], "stream": True},
                attributes={
                    "agent_name": agent.name,
                    "llm_provider": agent.llm.provider,
                    "llm_model": agent.llm.model
                },
                kind=SpanKind.SERVER
            )

            # Get LLM provider
            provider = self._get_provider(agent.llm)
            
            # Build messages
            messages = self._build_messages(
                agent,
                message,
                context,
                history,
                trace_id=trace_id,
                parent_span_id=agent_span.span_id if agent_span else None
            )
            
            # TODO: Load tools if agent has tools configured
            tools = None
            
            # Stream response
            logger.info(f"Streaming agent '{agent.id}' with provider '{agent.llm.provider}'")
            async for chunk in provider.stream_generate(messages, tools, **kwargs):
                yield chunk

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Store trace-level output for Langfuse (best-effort)
            try:
                if hasattr(self.telemetry_service, 'langfuse_service') and self.telemetry_service.langfuse_service.enabled:
                    self.telemetry_service.langfuse_service.update_trace(
                        trace_id,
                        output={
                            "stream": True,
                            "duration_seconds": duration,
                        }
                    )
            except Exception:
                pass

            self.telemetry_service.complete_action(
                span_id=agent_span.span_id,
                status=SpanStatus.OK,
                output_data={"stream": True, "duration_seconds": duration}
            )
            self.telemetry_service.end_trace(trace_id, SpanStatus.OK)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error streaming agent: {e}")
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            if 'trace_id' in locals():
                try:
                    self.telemetry_service.end_trace(trace_id, SpanStatus.ERROR)
                except Exception:
                    pass
            raise AgentExecutionError(f"LLM API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error streaming agent: {e}", exc_info=True)
            if 'trace_id' in locals():
                try:
                    self.telemetry_service.end_trace(trace_id, SpanStatus.ERROR)
                except Exception:
                    pass
            raise AgentExecutionError(f"Streaming failed: {str(e)}")


# Singleton instance
_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get the agent executor singleton."""
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor

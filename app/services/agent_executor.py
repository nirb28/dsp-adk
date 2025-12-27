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
from ..models.auth import AuthenticatedUser

logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Exception raised during agent execution."""
    pass


class LLMProvider:
    """Base class for LLM provider integrations."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        if self.config.api_key_env:
            return os.getenv(self.config.api_key_env)
        return None
    
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
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        if tools:
            payload["tools"] = tools
        
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
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
        
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
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build the messages array for the LLM."""
        messages = []
        
        # System prompt
        system_prompt = agent.llm.system_prompt
        if not system_prompt and hasattr(agent, 'system_prompt'):
            system_prompt = getattr(agent, 'system_prompt', None)
        
        if system_prompt:
            messages.append({
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
    
    async def run(
        self,
        agent: AgentConfig,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user: Optional[AuthenticatedUser] = None,
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
            **kwargs: Additional parameters for LLM
            
        Returns:
            Dict with response, usage, and metadata
        """
        try:
            start_time = datetime.utcnow()
            
            # Get LLM provider
            provider = self._get_provider(agent.llm)
            
            # Build messages
            messages = self._build_messages(agent, message, context, history)
            
            # TODO: Load tools if agent has tools configured
            tools = None
            
            # Generate response
            logger.info(f"Executing agent '{agent.id}' with provider '{agent.llm.provider}'")
            response = await provider.generate(messages, tools, **kwargs)
            
            # Extract response content
            content = ""
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "response": content,
                "usage": response.get("usage", {}),
                "model": agent.llm.model,
                "provider": agent.llm.provider,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
                "agent_id": agent.id,
                "agent_name": agent.name,
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing agent: {e}")
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise AgentExecutionError(f"LLM API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error executing agent: {e}", exc_info=True)
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
            # Get LLM provider
            provider = self._get_provider(agent.llm)
            
            # Build messages
            messages = self._build_messages(agent, message, context, history)
            
            # TODO: Load tools if agent has tools configured
            tools = None
            
            # Stream response
            logger.info(f"Streaming agent '{agent.id}' with provider '{agent.llm.provider}'")
            async for chunk in provider.stream_generate(messages, tools, **kwargs):
                yield chunk
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error streaming agent: {e}")
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise AgentExecutionError(f"LLM API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error streaming agent: {e}", exc_info=True)
            raise AgentExecutionError(f"Streaming failed: {str(e)}")


# Singleton instance
_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get the agent executor singleton."""
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor

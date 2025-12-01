"""
LLM Service - Multi-Provider Abstraction Layer

This module provides a unified interface for interacting with different LLM providers
(Anthropic Claude, OpenAI, Azure OpenAI). It handles:
- Provider-agnostic API calls
- Automatic retries with exponential backoff
- Error handling and logging
- JSON mode for structured outputs
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when hitting rate limits."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API returns an error."""
    pass


class LLMResponseParseError(LLMError):
    """Raised when response parsing fails."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            json_mode: If True, request JSON output format
            
        Returns:
            Generated text response
        """
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
        except ImportError:
            raise LLMError("anthropic package not installed. Run: pip install anthropic")
    
    @retry(
        retry=retry_if_exception_type(LLMRateLimitError),
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        import anthropic
        
        # Extract system message if present
        system_message = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        # Add JSON instruction if json_mode is enabled
        if json_mode and system_message:
            system_message += "\n\nYou must respond with valid JSON only. No additional text."
        elif json_mode:
            system_message = "You must respond with valid JSON only. No additional text."
        
        try:
            kwargs = {
                "model": settings.LLM_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages,
            }
            if system_message:
                kwargs["system"] = system_message
            
            response = self.client.messages.create(**kwargs)
            
            content = response.content[0].text
            logger.info(
                f"Anthropic API call successful. "
                f"Input tokens: {response.usage.input_tokens}, "
                f"Output tokens: {response.usage.output_tokens}"
            )
            return content
            
        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit hit: {e}")
            raise LLMRateLimitError(str(e))
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMAPIError(str(e))


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.LLM_API_KEY)
        except ImportError:
            raise LLMError("openai package not installed. Run: pip install openai")
    
    @retry(
        retry=retry_if_exception_type(LLMRateLimitError),
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        from openai import RateLimitError, APIError
        
        try:
            kwargs = {
                "model": settings.LLM_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            logger.info(
                f"OpenAI API call successful. "
                f"Input tokens: {response.usage.prompt_tokens}, "
                f"Output tokens: {response.usage.completion_tokens}"
            )
            return content
            
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise LLMRateLimitError(str(e))
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMAPIError(str(e))


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation."""
    
    def __init__(self):
        try:
            from openai import AzureOpenAI
            
            if not settings.AZURE_OPENAI_ENDPOINT:
                raise LLMError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI")
            
            self.client = AzureOpenAI(
                api_key=settings.LLM_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            )
            self.deployment = settings.AZURE_OPENAI_DEPLOYMENT or settings.LLM_MODEL
        except ImportError:
            raise LLMError("openai package not installed. Run: pip install openai")
    
    @retry(
        retry=retry_if_exception_type(LLMRateLimitError),
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        from openai import RateLimitError, APIError
        
        try:
            kwargs = {
                "model": self.deployment,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            logger.info(
                f"Azure OpenAI API call successful. "
                f"Input tokens: {response.usage.prompt_tokens}, "
                f"Output tokens: {response.usage.completion_tokens}"
            )
            return content
            
        except RateLimitError as e:
            logger.warning(f"Azure OpenAI rate limit hit: {e}")
            raise LLMRateLimitError(str(e))
        except APIError as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise LLMAPIError(str(e))


class LLMService:
    """
    Unified LLM service that provides a provider-agnostic interface.
    
    Usage:
        llm = LLMService()
        response = await llm.generate_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
    """
    
    _instance: Optional["LLMService"] = None
    _provider: Optional[BaseLLMProvider] = None
    
    def __new__(cls):
        """Singleton pattern to reuse the same provider instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._provider is None:
            self._provider = self._create_provider()
    
    def _create_provider(self) -> BaseLLMProvider:
        """Create the appropriate provider based on settings."""
        provider_map = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "azure_openai": AzureOpenAIProvider,
        }
        
        provider_class = provider_map.get(settings.LLM_PROVIDER.lower())
        if not provider_class:
            raise LLMError(
                f"Unknown LLM provider: {settings.LLM_PROVIDER}. "
                f"Available options: {list(provider_map.keys())}"
            )
        
        logger.info(f"Initializing LLM provider: {settings.LLM_PROVIDER}")
        return provider_class()
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a completion using the configured LLM provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Supported roles: system, user, assistant
            max_tokens: Maximum tokens in response (defaults to settings.LLM_MAX_TOKENS)
            temperature: Sampling temperature (defaults to settings.LLM_TEMPERATURE)
            json_mode: If True, request JSON output format
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: Base error for all LLM issues
            LLMRateLimitError: When rate limited (after retries exhausted)
            LLMAPIError: When API returns an error
        """
        return await self._provider.generate_completion(
            messages=messages,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            temperature=temperature or settings.LLM_TEMPERATURE,
            json_mode=json_mode,
        )
    
    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM.
        
        Args:
            messages: List of message dicts
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            LLMResponseParseError: If response is not valid JSON
        """
        response = await self.generate_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=True,
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response[:200]}...")
            raise LLMResponseParseError(f"Invalid JSON response: {e}")


# Convenience function to get the LLM service instance
def get_llm_service() -> LLMService:
    """Get the singleton LLM service instance."""
    return LLMService()


"""
Modular LLM service supporting multiple providers (OpenAI, Anthropic, local models)
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass

# LLM Provider imports
import openai
import anthropic
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    usage: Dict[str, int]
    model: str
    provider: str
    finish_reason: str
    metadata: Dict[str, Any]


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from LLM"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.provider_name = "openai"
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            choice = response.choices[0]
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=choice.message.content,
                usage=usage,
                model=response.model,
                provider=self.provider_name,
                finish_reason=choice.finish_reason,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo-preview"
        ]


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.provider_name = "anthropic"
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic API"""
        try:
            # Convert OpenAI format to Anthropic format
            system_message = ""
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] in ["user", "assistant"]:
                    claude_messages.append(msg)
            
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=claude_messages,
                **kwargs
            )
            
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=response.content[0].text,
                usage=usage,
                model=response.model,
                provider=self.provider_name,
                finish_reason=response.stop_reason,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Anthropic API"""
        try:
            # Convert OpenAI format to Anthropic format
            system_message = ""
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] in ["user", "assistant"]:
                    claude_messages.append(msg)
            
            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=claude_messages,
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models"""
        return [
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ]


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider (placeholder for future implementation)"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.provider_name = "local"
        # TODO: Implement local model loading (e.g., using transformers, ollama, etc.)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate response using local model"""
        # Placeholder implementation
        # TODO: Implement actual local model inference
        response_text = "This is a placeholder response from local LLM. Please implement actual local model inference."
        
        return LLMResponse(
            content=response_text,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model=model,
            provider=self.provider_name,
            finish_reason="stop",
            metadata={}
        )
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using local model"""
        # Placeholder implementation
        response_text = "This is a placeholder streaming response from local LLM."
        for word in response_text.split():
            yield word + " "
    
    def get_available_models(self) -> List[str]:
        """Get list of available local models"""
        return ["local-model"]


class LLMService:
    """
    Main LLM service that manages multiple providers and handles RAG responses
    """
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
        self.default_provider = settings.default_llm_provider
    
    def _initialize_providers(self):
        """Initialize available LLM providers"""
        # Initialize OpenAI provider
        if settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(settings.openai_api_key)
            logger.info("OpenAI provider initialized")
        
        # Initialize Anthropic provider
        if settings.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
            logger.info("Anthropic provider initialized")
        
        # Initialize local provider (placeholder)
        self.providers["local"] = LocalLLMProvider()
        logger.info("Local provider initialized (placeholder)")
    
    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """Get LLM provider by name"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available")
        return self.providers[provider_name]
    
    def build_rag_prompt(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build RAG prompt with retrieved context
        """
        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant. Use the provided context to answer the user's question accurately and comprehensively. If the context doesn't contain enough information to answer the question, please say so clearly.

Guidelines:
- Base your answer primarily on the provided context
- Be factual and precise
- If you're uncertain about something, acknowledge it
- Cite relevant parts of the context when appropriate
- If the context is insufficient, clearly state that limitation"""
        
        # Build context section
        context_text = ""
        if context_documents:
            context_text = "\n\nContext Documents:\n"
            for i, doc in enumerate(context_documents, 1):
                source = doc.get("source", "Unknown")
                text = doc.get("text", "")
                context_text += f"\n[Document {i} - {source}]\n{text}\n"
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {query}{context_text}"}
        ]
        
        return messages
    
    async def generate_rag_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        provider: str = None,
        model: str = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """
        Generate RAG response with retrieved context
        """
        # Use default provider if not specified
        if provider is None:
            provider = self.default_provider
        
        # Get provider instance
        llm_provider = self.get_provider(provider)
        
        # Use default model for provider if not specified
        if model is None:
            available_models = llm_provider.get_available_models()
            model = available_models[0] if available_models else "default"
        
        # Build RAG prompt
        messages = self.build_rag_prompt(query, context_documents, system_prompt)
        
        # Generate response
        if stream:
            return llm_provider.generate_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            return await llm_provider.generate_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        if provider not in self.providers:
            return []
        return self.providers[provider].get_available_models()
"""LLM Provider Factory with fallback support"""

from typing import Optional, List
import os
from loguru import logger
from langchain_core.language_models import BaseChatModel


class LLMProvider:
    """Unified LLM provider with automatic fallback"""

    def __init__(self, providers: Optional[List[str]] = None):
        """
        Initialize LLM provider

        Args:
            providers: Ordered list of providers to try (default: ['ollama', 'openai', 'anthropic'])
        """
        self.providers = providers or ['ollama', 'openai', 'anthropic']
        self.llm: Optional[BaseChatModel] = None
        self.active_provider: Optional[str] = None

    def get_llm(self, temperature: float = 0.7) -> Optional[BaseChatModel]:
        """
        Get LLM with automatic fallback

        Args:
            temperature: Sampling temperature (0.0 - 1.0)

        Returns:
            LLM instance or None if all providers failed
        """

        for provider in self.providers:
            try:
                if provider == 'ollama' and os.getenv("OLLAMA_BASE_URL"):
                    llm = self._init_ollama(temperature)
                    if llm:
                        self.llm = llm
                        self.active_provider = 'ollama'
                        logger.info(f"✓ Using Ollama: {os.getenv('OLLAMA_MODEL', 'llama3.1')}")
                        return self.llm

                elif provider == 'openai' and os.getenv("OPENAI_API_KEY"):
                    llm = self._init_openai(temperature)
                    if llm:
                        self.llm = llm
                        self.active_provider = 'openai'
                        logger.info(f"✓ Using OpenAI: {os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')}")
                        return self.llm

                elif provider == 'anthropic' and os.getenv("ANTHROPIC_API_KEY"):
                    llm = self._init_anthropic(temperature)
                    if llm:
                        self.llm = llm
                        self.active_provider = 'anthropic'
                        logger.info(f"✓ Using Anthropic: {os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229')}")
                        return self.llm

                elif provider == 'groq' and os.getenv("GROQ_API_KEY"):
                    llm = self._init_groq(temperature)
                    if llm:
                        self.llm = llm
                        self.active_provider = 'groq'
                        logger.info(f"✓ Using Groq: {os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')}")
                        return self.llm

            except Exception as e:
                logger.warning(f"Failed to initialize {provider}: {e}")
                continue

        logger.warning("No LLM providers available. System will use fallback responses.")
        return None

    def _init_ollama(self, temperature: float) -> Optional[BaseChatModel]:
        """Initialize Ollama"""
        try:
            from langchain_ollama import ChatOllama

            return ChatOllama(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "llama3.1"),
                temperature=temperature
            )
        except ImportError:
            logger.warning("langchain-ollama not installed")
            return None
        except Exception as e:
            logger.warning(f"Ollama initialization failed: {e}")
            return None

    def _init_openai(self, temperature: float) -> Optional[BaseChatModel]:
        """Initialize OpenAI"""
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except ImportError:
            logger.warning("langchain-openai not installed")
            return None
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
            return None

    def _init_anthropic(self, temperature: float) -> Optional[BaseChatModel]:
        """Initialize Anthropic"""
        try:
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        except ImportError:
            logger.warning("langchain-anthropic not installed")
            return None
        except Exception as e:
            logger.warning(f"Anthropic initialization failed: {e}")
            return None

    def _init_groq(self, temperature: float) -> Optional[BaseChatModel]:
        """Initialize Groq"""
        try:
            from langchain_groq import ChatGroq

            return ChatGroq(
                model=os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
                temperature=temperature,
                api_key=os.getenv("GROQ_API_KEY")
            )
        except ImportError:
            logger.warning("langchain-groq not installed")
            return None
        except Exception as e:
            logger.warning(f"Groq initialization failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if any LLM is available"""
        return self.llm is not None

    def get_provider_name(self) -> Optional[str]:
        """Get active provider name"""
        return self.active_provider

    def reinitialize(self, providers: Optional[List[str]] = None) -> bool:
        """
        Reinitialize with different provider order

        Args:
            providers: New provider order

        Returns:
            True if initialization successful
        """
        if providers:
            self.providers = providers

        self.llm = None
        self.active_provider = None

        return self.get_llm() is not None

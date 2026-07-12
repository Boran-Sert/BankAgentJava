"""Provides core functionalities for the llm_factory module."""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from app.core.config import settings
from app.core.logger import logger

class LLMFactory:
    """
    Factory pattern to generate the appropriate LLM based on centralized settings.
    Ensures that the LLM object adheres to the LangChain BaseChatModel standard,
    fully supporting bind_tools() and native tool calling.
    """
    
    @staticmethod
    def get_llm() -> BaseChatModel:
        """Returns the configured LLM engine."""
        
        mode = settings.llm.mode.lower()
        
        if mode == "gpt-oss":
            logger.info("initializing_llm", mode="gpt-oss", base_url=settings.llm.gpt_oss_base_url)
            return ChatOpenAI(
                base_url=settings.llm.gpt_oss_base_url,
                api_key=settings.llm.gpt_oss_api_key,
                temperature=settings.llm.temperature,
                # Optionally add model name if required by GPT-OSS endpoint
                model="gpt-oss-120b" 
            )
        elif mode == "ollama":
            logger.info("initializing_llm", mode="ollama", model=settings.llm.ollama_model)
            return ChatOllama(
                model=settings.llm.ollama_model,
                temperature=settings.llm.temperature,
                base_url="http://127.0.0.1:11434",
                # ChatOllama supports native tool calling in recent versions
            )
        else:
            error_msg = f"Unsupported LLM mode specified in config: {mode}"
            logger.error("llm_initialization_failed", error=error_msg)
            raise ValueError(error_msg)

# Singleton instance for easy import across the application
llm_engine = LLMFactory.get_llm()

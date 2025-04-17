"""
Module to connect with LLM.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_together import ChatTogether
from langchain_core.prompts import ChatPromptTemplate
from util import read_gpg_encrypted_file

class LLMManager:
    """
    LLMManager is responsible for initializing and managing connections to different
    LLM providers (e.g., OpenAI, Anthropic, etc.).

    Currently supported:
    - OpenAI (GPT-3.5, GPT-4, GPT-4o)

    Usage: update the configuration in llm_config.json
    -------
    config = {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key_path": "sensitive/openai.txt",
    }
    """
    def __init__(self, config: dict):
        self.provider = config.get("provider", "openai").lower()

        if self.provider == "openai":
            self.llm = self._init_openai(config)
        elif self.provider == "togetherai":
            self.llm = self._init_togetherai(config)
        else:
            raise NotImplementedError(f"LLM provider '{self.provider}' is not yet supported.")

    def _init_openai(self, config):
        api_key_path = config.get("api_key_path")
        env_var = config.get("env_var", "OPENAI_API_KEY")

        if api_key_path:
            key = read_gpg_encrypted_file(api_key_path)
            os.environ["OPENAI_API_KEY"] = key
        elif os.environ.get(env_var):
            os.environ["OPENAI_API_KEY"] = os.environ[env_var]
        else:
            raise ValueError("OpenAI API key not provided")

        model = config.get("model", "gpt-3.5-turbo")

        return ChatOpenAI(model=model, temperature=0)

    def _init_togetherai(self, config):
        api_key_path = config.get("api_key_path")
        env_var = config.get("env_var", "TOGETHER_API_KEY")
        if api_key_path:
            key = read_gpg_encrypted_file(api_key_path)
            os.environ["TOGETHER_API_KEY"] = key
        elif os.environ.get(env_var):
            os.environ["TOGETHER_API_KEY"] = os.environ[env_var]
        else:
            raise ValueError("Together AI API key not provided")

        model = config.get("model", "meta-llama/Llama-3-8b-chat-hf")

        return ChatTogether(model=model, temperature=0)

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        response = self.llm.invoke(messages)
        return response.content

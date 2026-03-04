"""
Module to connect with LLM.
"""
import os
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
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
        self._mcp_client = None

        if self.provider == "openai":
            self.llm = self._init_openai(config)
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

    def _get_mcp_server_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "mcp-server" / "server.py"

    def get_mcp_client(self) -> MultiServerMCPClient:
        if self._mcp_client is not None:
            return self._mcp_client

        server_path = self._get_mcp_server_path()
        if not server_path.exists():
            raise FileNotFoundError(f"MCP server not found at {server_path}")

        self._mcp_client = MultiServerMCPClient(
            {
                "local_mcp": {
                    "transport": "stdio",
                    "command": sys.executable,
                    "args": [str(server_path)],
                }
            }
        )
        return self._mcp_client

    async def get_mcp_tools(self, client: MultiServerMCPClient = None):
        if client is None:
            client = self.get_mcp_client()
        return await client.get_tools()

    async def build_mcp_agent(self, llm=None, tools=None):
        if llm is None:
            llm = self.llm
        if tools is None:
            tools = await self.get_mcp_tools()
        return create_react_agent(llm, tools)

    async def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        # messages = prompt.format_messages(**kwargs)
        # response = self.llm.invoke(messages)
        # return response.content

        messages = prompt.format_messages(**kwargs)
        llm_mcp = self.build_mcp_agent()
        response = llm_mcp.invoke(messages)
        return response.content

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from ServiceManager import ServiceManager
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.base import Chain
import gnupg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import argparse
import time
from pathlib import Path
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_classic.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables.base import RunnableLambda
from summarizer import summarize_chat_history
from constants import *
from prompts import *

# GPG_BINARY_PATH = "/opt/homebrew/bin/gpg"
SENSITIVE_PATH = "sensitive/openai.txt"

# gpg = gnupg.GPG(binary=GPG_BINARY_PATH)
def read_json(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
    except json.JSONDecodeError:
        print(f"Error: File '{file_name}' is not a valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent
config_details = read_json(str(REPO_ROOT / "config.json"))
llm_config = read_json('llm_config.json')

app = FastAPI()

# Initialize the service manager
service_manager = ServiceManager(config_details, llm_config)
redis_client = service_manager.get_redis()
redis_client = redis_client.redis
db = service_manager.get_db()
llm = service_manager.get_llm()
llm_manager = service_manager.get_llm_manager()

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

class ChatMessage(BaseModel):
    session_id: str
    message: str
    message_type: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sql_query: Optional[str]
    query_result: Optional[str]
    history: List[dict]

def run_sql_chain(question: str, history: List[dict], session_id: str, memory: ConversationBufferMemory):
    """Run the SQL generation chain with conversation history"""
    table_info = db.get_table_info()
    messages = []

    HISTORY_THRESHOLD = 20

    system_messages = [msg for msg in history if isinstance(msg, SystemMessage)]
    chat_messages = [msg for msg in history if isinstance(msg, (HumanMessage, AIMessage))]

    if len(chat_messages) > HISTORY_THRESHOLD:
        print("###debug the old history ###", chat_messages)
        summary_data = summarize_chat_history(chat_messages, llm)

        summary_message = SystemMessage(content=summary_data["summary"])
        new_history = [summary_message] + summary_data["messages"]
        print("Conversation history was summarized due to length.")
        # Update Redis cache: delete old history and set the new summarized history
        redis_client.delete(f"chat:{session_id}")
        for msg in new_history:
            redis_client.rpush(f"chat:{session_id}", json.dumps(msg.model_dump(mode="json")))
        # Update the local history variable to use in the prompt
        history = system_messages + new_history
        print("debug new history: ", history)

    # Retrieve system message from Redis to ensure table info is always present in the sql generation chain message
    system_message_from_redis = redis_client.smembers(f"system_message:{session_id}")
    if system_message_from_redis:
        system_message_content = list(system_message_from_redis)[0]  # Assuming only one system message
        system_message = SystemMessage(content=json.loads(system_message_content)["content"])
        messages.insert(0, system_message)


    if not history:
        # For initial prompt (no history)
        initial_prompt_value = INITIAL_PROMPT.invoke({
            "table_info": table_info,
            "top_k": TOP_K_ROWS
        })
        continuation_prompt_value = CONTINUATION_PROMPT.invoke({
            "question": question,
            "history": []
        })
        messages.extend(initial_prompt_value.messages)
        messages.extend(continuation_prompt_value.messages)
        update_chat_memory_and_redis_history(session_id, initial_prompt_value.messages[0].content,
                                                "system", memory)
    else:
        # For continuation prompt (with history)
        continuation_prompt_value = CONTINUATION_PROMPT.invoke({
            "question": question,
            "history": history
        })
        messages.extend(continuation_prompt_value.messages)

    # Ensure all messages are of type BaseMessage with correct types
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            formatted_messages.insert(0, msg)  # Ensure system message is at the start
        elif isinstance(msg, HumanMessage):
            formatted_messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            formatted_messages.append(AIMessage(content=msg.content))

    # Create the SQL generation chain
    sql_generation_chain = (
        RunnableLambda(lambda x: x)  # Pass messages directly
        | llm
    )

    # Invoke the chain
    result = sql_generation_chain.invoke(formatted_messages)

    # Store updated history in Redis
    for msg in messages:
        # Check message type
        message_type = ""
        message = msg.content
        if isinstance(msg, SystemMessage):
            message_type="system"
            update_chat_memory_and_redis_history(session_id, message,
                                                message_type, memory)

    update_chat_memory_and_redis_history(session_id, question,
                                                "human", memory)

    memory = update_chat_memory_and_redis_history(session_id, result.content,
                                                  "ai", memory)
    return (result, memory)

async def run_mcp_chain(question: str, history: List[dict], session_id: str, memory: ConversationBufferMemory):
    """Run the MCP-only chain with conversation history.

    Tool surface is defined in ``mcp-server/server.py`` (e.g. shootings, unemployment, FAA aircraft)
    and described for the model in ``prompts.MCP_SYSTEM_PROMPT`` / ``MCP_PROMPT``.
    """
    messages = []

    HISTORY_THRESHOLD = 20

    system_messages = [msg for msg in history if isinstance(msg, SystemMessage)]
    chat_messages = [msg for msg in history if isinstance(msg, (HumanMessage, AIMessage))]

    if len(chat_messages) > HISTORY_THRESHOLD:
        summary_data = summarize_chat_history(chat_messages, llm)

        summary_message = SystemMessage(content=summary_data["summary"])
        new_history = [summary_message] + summary_data["messages"]
        print("Conversation history was summarized due to length.")
        # Update Redis cache: delete old history and set the new summarized history
        redis_client.delete(f"chat:{session_id}")
        for msg in new_history:
            redis_client.rpush(f"chat:{session_id}", json.dumps(msg.model_dump(mode="json")))
        # Update the local history variable to use in the prompt
        history = system_messages + new_history

    table_info = db.get_table_info()
    prompt_value = MCP_PROMPT.invoke({
        "table_info": table_info,
        "question": question,
        "history": history
    })
    messages.extend(prompt_value.messages)

    # Ensure all messages are of type BaseMessage with correct types
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            formatted_messages.insert(0, msg)  # Ensure system message is at the start
        elif isinstance(msg, HumanMessage):
            formatted_messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            formatted_messages.append(AIMessage(content=msg.content))

    tools = await llm_manager.get_mcp_tools()
    agent = await llm_manager.build_mcp_agent(llm=llm, tools=tools)
    result = await agent.ainvoke({"messages": formatted_messages})
    result_messages = result.get("messages", [])
    final_message = None
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage):
            final_message = msg
            break
    if final_message is None:
        raise RuntimeError("MCP agent returned no AI message.")

    for msg in messages:
        if isinstance(msg, SystemMessage):
            update_chat_memory_and_redis_history(session_id, msg.content, "system", memory)

    update_chat_memory_and_redis_history(session_id, question, "human", memory)
    memory = update_chat_memory_and_redis_history(session_id, final_message.content, "ai", memory)
    return (final_message, memory, result_messages)

# Define the request body model using Pydantic
class ChatRequest(BaseModel):
    session_id: int
    message: str
    message_type: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    sql_query: Optional[str]
    sql_valid: bool
    query_result: Optional[str]

def get_message_history(session_id: str) -> ConversationBufferMemory:
    """Retrieve chat history for a session from Redis cache"""
    memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=True
    )

    redis_key = f"chat:{session_id}"
    system_key = f"system_message:{session_id}"

    cached_messages = redis_client.lrange(redis_key, 0, -1)
    system_messages = redis_client.smembers(system_key)

    parsed_system_messages = []
    for msg in system_messages:
        if not msg:
            continue
        try:
            decoded_msg = msg.decode("utf-8") if isinstance(msg, bytes) else msg
            parsed_msg = json.loads(decoded_msg)
            parsed_system_messages.append(parsed_msg)
        except json.JSONDecodeError:
            print(f"❌ JSONDecodeError while parsing system message: {msg}")
        except Exception as e:
            print(f"❌ Unexpected error decoding system message: {msg}, Error: {e}")

    print("✅ Successfully loaded system messages:")

    for msg in cached_messages:
        msg = json.loads(msg)
        if msg["type"] == "human":
            memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
        elif msg["type"] == "ai":
            memory.chat_memory.add_message(AIMessage(content=msg["content"]))

    return memory

def update_chat_memory_and_redis_history(session_id: str, message_content: str, message_type: str,
                                         memory: ConversationBufferMemory) -> ConversationBufferMemory:
    """Save updated chat history to Redis cache and memory object.
    We use chat:<session_id> for the Human and AI messages
    system_message<session_id> is used to store the system message"""

    redis_key = f"chat:{session_id}"
    system_message_key = f"system_message:{session_id}"  # Separate key for system messages

    if message_type == "system":
        if not redis_client.sismember(system_message_key, json.dumps({"type": "system", "content": message_content})):
            redis_client.sadd(system_message_key, json.dumps({"type": "system", "content": message_content}))
            print("✅ Stored System Message in Redis.")
    else:
        redis_client.rpush(redis_key, json.dumps({"type": message_type, "content": message_content}))
        print(f"✅ {message_type.capitalize()} message appended to session {session_id}.")

    redis_client.expire(redis_key, CHAT_HISTORY_TTL)
    redis_client.expire(system_message_key, CHAT_HISTORY_TTL)  # Expire system message key too
    print(f"🕒 TTL updated to {CHAT_HISTORY_TTL} seconds for session {session_id}")

    # Update conversation buffer memory
    if message_type == 'human':
        memory.chat_memory.add_message(HumanMessage(content=message_content))
    elif message_type == 'ai':
        memory.chat_memory.add_message(AIMessage(content=message_content))
    elif message_type == 'system':
        memory.chat_memory.add_message(SystemMessage(content=message_content))
    return memory

def extract_token_usage_from_message(message) -> Dict[str, Optional[int]]:
    usage = getattr(message, "usage_metadata", None) or {}
    response_metadata = getattr(message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage", {}) if isinstance(response_metadata, dict) else {}

    prompt_tokens = usage.get("input_tokens")
    completion_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")

    if prompt_tokens is None:
        prompt_tokens = token_usage.get("prompt_tokens") or token_usage.get("input_tokens")
    if completion_tokens is None:
        completion_tokens = token_usage.get("completion_tokens") or token_usage.get("output_tokens")
    if total_tokens is None:
        total_tokens = token_usage.get("total_tokens")

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def aggregate_token_usage(messages: List[BaseMessage]) -> Dict[str, Optional[int]]:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    found_usage = False

    for message in messages:
        if not isinstance(message, AIMessage):
            continue
        usage = extract_token_usage_from_message(message)
        if usage["prompt_tokens"] is not None:
            prompt_tokens += usage["prompt_tokens"]
            found_usage = True
        if usage["completion_tokens"] is not None:
            completion_tokens += usage["completion_tokens"]
            found_usage = True
        if usage["total_tokens"] is not None:
            total_tokens += usage["total_tokens"]
            found_usage = True

    if not found_usage:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }

    if total_tokens == 0 and prompt_tokens and completion_tokens:
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": prompt_tokens if prompt_tokens or prompt_tokens == 0 else None,
        "completion_tokens": completion_tokens if completion_tokens or completion_tokens == 0 else None,
        "total_tokens": total_tokens if total_tokens or total_tokens == 0 else None,
    }


def execute_sql_query(sql_query:str):
    execute_query = QuerySQLDataBaseTool(db=db)
    query_results = None
    error_message = None
    start_time = time.perf_counter()
    try:
        query_results = execute_query.invoke({"query": sql_query})
    except Exception as e:
        error_message = str(e)
        print(error_message)

    return {
        "query_results": query_results,
        "sql_execution_success": error_message is None and query_results is not None,
        "sql_execution_error": error_message,
        "sql_execution_latency_ms": round((time.perf_counter() - start_time) * 1000, 3),
    }

def is_mcp_only() -> bool:
    value = os.getenv("MCP_ONLY")
    if value is None:
        return True
    return value.strip() != "0"


def build_profiling_payload(
    mode: str,
    start_time: float,
    sql_execution_latency_ms: Optional[float] = None,
    token_usage: Optional[Dict[str, Optional[int]]] = None,
) -> dict:
    payload = {
        "mode": mode,
        "model_name": llm_config["llm"].get("model"),
        "server_handler_latency_ms": round((time.perf_counter() - start_time) * 1000, 3),
        "sql_execution_latency_ms": sql_execution_latency_ms,
    }

    token_usage = token_usage or {}
    payload["prompt_tokens"] = token_usage.get("prompt_tokens")
    payload["completion_tokens"] = token_usage.get("completion_tokens")
    payload["total_tokens"] = token_usage.get("total_tokens")
    return payload

# Define the POST request handler for sending the prompt
# remove chat response
# @app.post("/query", response_model=ChatResponse)
@app.post("/query")
async def handle_query(request: Request):
    json_data = await request.json()
    chat_request = ChatRequest(
        session_id=json_data["session_id"],
        message=json_data["question"],
        message_type=json_data["message_type"]
    )
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="No question provided")
    sql_query = None
    query_results = None
    memory = get_message_history(chat_request.session_id)
    mcp_only = is_mcp_only()
    mode = "mcp" if mcp_only else "text2sql"
    start_time = time.perf_counter()
    if mcp_only:
        try:
            result, memory, result_messages = await run_mcp_chain(
                chat_request.message,
                memory.load_memory_variables({})["history"],
                chat_request.session_id,
                memory
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "profiling": build_profiling_payload(mode, start_time),
                },
            )
        token_usage = aggregate_token_usage(result_messages)
        return {
            "response": result.content,
            "final_llm_response": result.content,
            "sql_query": None,
            "query_results": None,
            "sql_execution_success": None,
            "sql_execution_error": None,
            "profiling": build_profiling_payload(mode, start_time, token_usage=token_usage),
        }
    else:
        # Invoke the SQL chain with the question
        try:
            sql_result, memory = run_sql_chain(
                chat_request.message,
                memory.load_memory_variables({})["history"],
                chat_request.session_id,
                memory
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "profiling": build_profiling_payload(mode, start_time),
                },
            )
        token_usage = extract_token_usage_from_message(sql_result)
        content = sql_result.content
        if content.startswith('```sql') and content.endswith('```'):
            sql_query = content[6:-3].strip()  # Remove the markdown ```sql and ```
        else:
            sql_query = content.strip()

        query_results = execute_sql_query(
            sql_query
        )

        return {
            "final_llm_response": sql_result.content,
            "sql_query": sql_query,
            "query_results": query_results["query_results"],
            "sql_execution_success": query_results["sql_execution_success"],
            "sql_execution_error": query_results["sql_execution_error"],
            "profiling": build_profiling_payload(
                mode,
                start_time,
                sql_execution_latency_ms=query_results["sql_execution_latency_ms"],
                token_usage=token_usage,
            ),
        }

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp-only", action="store_true", help="Run with MCP-only prompt and responses.")
    args = parser.parse_args()
    if args.mcp_only:
        os.environ["MCP_ONLY"] = "1"
    uvicorn.run(app, host="0.0.0.0", port=8000)

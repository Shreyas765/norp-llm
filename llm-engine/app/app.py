from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from ServiceManager import ServiceManager
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.base import Chain
import gnupg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
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
config_details = read_json('config.json')

app = FastAPI()

# Initialize the service manager
service_manager = ServiceManager(config_details)
redis_client = service_manager.get_redis()
redis_client = redis_client.redis
db = service_manager.get_db()
llm = service_manager.get_llm()

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

    HISTORY_THRESHOLD = 100
    if len(history) > HISTORY_THRESHOLD:
        summary_data = summarize_chat_history(history, llm)
        
        summary_message = SystemMessage(content=summary_data["summary"])
        new_history = [summary_message] + summary_data["messages"]
        print("Conversation history was summarized due to length.")
        # Update Redis cache: delete old history and set the new summarized history
        redis_client.delete(f"chat:{session_id}")
        for msg in new_history:
            redis_client.rpush(f"chat:{session_id}", json.dumps(msg.model_dump(mode="json")))
        # Update the local history variable to use in the prompt
        history = new_history
    
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
        if isinstance(msg, dict):
            msg_type = msg.get("type", "human")  # Default to "human" if type is missing
            content = msg.get("content", "")

            if msg_type == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif msg_type == "human":
                formatted_messages.append(HumanMessage(content=content))
        elif isinstance(msg, BaseMessage):
            # If already a BaseMessage, add directly
            formatted_messages.append(msg)
        else:
            raise ValueError(f"Unexpected message format: {msg}")

    # Create the SQL generation chain
    sql_generation_chain = (
        RunnableLambda(lambda x: x)  # Pass messages directly
        | llm
    )
    
    # Invoke the chain
    result = sql_generation_chain.invoke(formatted_messages)

    # update redis and history
    for msg in messages:
        # Check message type
        message_type = ""
        message = msg.content
        if isinstance(msg, SystemMessage):
            message_type="system"
        elif isinstance(msg, HumanMessage):
            message_type="human"
        elif isinstance(msg, AIMessage):
            message_type="ai"
        elif isinstance(msg, MessagesPlaceholder):
            continue
        if message_type and message:
           update_chat_memory_and_redis_history(session_id, message, 
                                                message_type, memory)

    memory = update_chat_memory_and_redis_history(session_id, result.content, 
                                                  "ai", memory)
    return (result, memory)
    

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
        redis_client.sadd(system_message_key, json.dumps({"type": "system", "content": message_content}))
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

def execute_sql_query(sql_query:str):
    execute_query = QuerySQLDataBaseTool(db=db)
    query_results=None
    try:
        query_results = execute_query.invoke({"query": sql_query})
    except Exception as e:
        # TODO: Add feedback loop here when memory issue is sorted
        error_message = str(e)
        print(error_message)
    return query_results

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
    # Invoke the chain with the question
    try:
        sql_query, memory = run_sql_chain(
            chat_request.message,
            memory.load_memory_variables({})["history"],
            chat_request.session_id,
            memory
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    content = sql_query.content
    if content.startswith('```sql') and content.endswith('```'):
        sql_query = content[6:-3].strip()  # Remove the markdown ```sql and ```
    else:
        sql_query = content.strip()
    
    query_results = execute_sql_query(
        sql_query
    )

    return {"sql_query": sql_query, "query_results": query_results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

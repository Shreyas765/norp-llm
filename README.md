# norp-llm
# SQL Chatbot Application

This application is a chatbot that interacts with users, generates SQL queries based on natural language input, and executes those queries on a database. It uses **LangChain** for conversational AI, **FastAPI** for the API, and **Redis** for session management.

---

## Features

- **Chatbot Interaction**: Conversational interface for users to ask SQL-related questions.
- **SQL Query Generation**: Automatically constructs SQL queries from user input.
- **Database Integration**: Executes queries against a connected database and retrieves results.
- **Session Management**: Maintains conversational context using Redis.
- **RESTful API**: Easy integration with other systems.

---

## Prerequisites

### Software Requirements
- Python 3.9 or higher
- Redis server
- A running SQL database (e.g., MySQL, PostgreSQL)

## Setup

Use the provided devcontainer to spin up a consistent dev environment plus local MariaDB and Redis services.

### Requirements
- Docker Desktop (or Docker Engine + Docker Compose)
- Visual Studio Code
- VS Code Dev Containers extension

### Devcontainer steps (VS Code)
1. Open this repo in VS Code.
2. Ensure Docker is running.
3. Run the command `Dev Containers: Reopen in Container`.
4. VS Code will build the devcontainer defined in [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) and start services from [.devcontainer/docker-compose.yml](.devcontainer/docker-compose.yml).
5. Wait for the container to finish its setup (it installs Python dependencies and keeps the container running).

For using an OpenAI token, create a folder named `sensitive` and a file `sensitive/openai.txt` that holds the OpenAI key. Similarly for other LLM providers, we recommend using a `sensitive/{provider}.txt` folder

The file `config.json` holds the details for the SQL and Redis connections. The descriptions of the fields are given below

```json
{
  "db_url": "The database URL which follows the schema mysql+mysqlconnector://{username}:{password}@{host}/{database_name}",
  "db_username": "The username of the database",
  "db_password": "The password of the database",
  "redis_host_url": "The URL of the Redis host instance",
  "redis_port": "(int) The port on which the Redis instance is being hosted",
  "redis_password": "(Optional) The password of the Redis instance if authentication is enabled"
}
```

## Setting up the Redis instance
In order to set up the Redis instance, simply connect the port number to the `llm-engine/app/RedisManager.py` and `config.json`.

## Running the app
## Running the MCP server
Start the MCP server before running the app:
```
python mcp-server/server.py
```

To run the server, use the following command
```
cd ./llm-engine/app
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Setting up the MySQL database connection
Simply connect the Database URL and password from `config.json` or environment variables and update `llm-engine/app/DatabaseManager.py` if needed.
You can also connect to local MySQL Database by passing the relevant URL to ServiceManager.


## Hitting the app with API requests
First approach is using a CURL command after the app is running.
```
Invoke-RestMethod -Uri "http://127.0.0.1:8000/query" `

  -Method Post `

  -ContentType "application/json" `

  -Body '{"question": "Give me the number of employees who are male", "session_id": 12345, "message_type": "human"}'
```
Another approach is to run `test_responses.py` script.
```
python test_responses.py --question "For each month, get count of victims killed and average of victims killed in each shooting incident." --session_id 585
```

## Local Setup
1. To test locally setup local MySQL Database and Redis instance in desired way and ensure to connect the port numbers and relevant URLs.
2. Now, run `create_NORP_tables.py` to create local sample tables after filling
in the correct details for the database username and password.
3. Run the app using `uvicorn app:app --reload --host 127.0.0.1 --port 8000`
4. Use `test_responses.py` script to see the results.
---

### Summarizer Threshold Configuration
The threshold for running summarization on the conversation history can be done by adjusting the `HISTORY_THRESHOLD` variable in the main [app file](llm-engine/app/app.py), in [this line](https://github.gatech.edu/NORP/norp-llm/blob/6a87490b0ec37c03ba8953acffd6396823eb263f/llm-engine/app/app.py#L73) as of writing (Apr 2025).


### Changing the LLM Provider
---
Users can specify what LLM Provider to use and as long as they specify where the corresponding API key is stored, preferably in a `sensitive/*` folder path inside the `llm-engine/app` folder, by specifying it in a configuration file called [`llm_config.json`](llm-engine/app/llm_config.json) inside the `llm-engine/app` folder. An example is as follows:

```json
{
    "llm": {
      "provider": "togetherai",
      "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
      "api_key_path": "sensitive/togetherai.txt"
    }
}
```
---

### Prompts for Testing the App

The standardized list of prompts used for testing and benchmarking are provided in [this spreadsheet](https://docs.google.com/spreadsheets/d/1EtjVqZ7lMCZYupPAFsDUoGma4EZeQ5htg_wDhnkPr0g/edit?usp=sharing)

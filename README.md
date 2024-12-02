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

Create an environment using pip, activate the environment and install the required Python libraries using `pip`.

```bash
conda create -n NORP_llm python=3.9
conda activate NORP_LLM
pip install -r requirements.txt
```

For using an OpenAI token, create a folder named `sensitive` and a file `sensitive/openai.txt` that holds the OpenAI key.

The file `llm-engine/app/config.json` holds the details for the SQL and Redis connections. The descriptions of the fields are given below
```json
{
  "db_url": "The database URL",
  "db_username": "The username of the database",
  "db_password": "The password of the database",
  "redis_host_url": "The URL of the Redis host instance",
  "redis_port": "(int) The port on which the Redis instance is being hosted"
}
```
## Setting up the Redis instance
In order to set up the Redis instance, simply connect the port number to the `llm-engine/app/RedisManager.py` and `llm-engine/app/config.json`.

## Running the app
To run the server, use the following command
```
cd ./llm-engine/app
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Setting up the MySQL database connection
Simply connect the Database URL and password from `llm-engine/app/config.json` or environment variables and update `llm-engine/app/DatabaseManager.py` if needed.
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
python .\test_responses.py --question "For each month, get count of victims killed and average of victims killed in each shooting incident." --session_id 585
```

## Local Setup
1. To test locally setup local MySQL Database and Redis instance in desired way and ensure to connect the port numbers and relevant URLs.
2. Now, run `create_NORP_tables.py` to create local sample tables.
3. Run the app using `uvicorn app:app --reload --host 127.0.0.1 --port 8000`
4. Use `test_responses.py` script to see the results.
---


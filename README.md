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

## Setting up the Redis instance
In order to set up the Redis instance, use the following commands
```
```

## Running the app
To run the server, use the following command
```
cd ./llm-engine/app
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Setting up the MySQL database connection

```
```
---


## Hitting the app with API requests

```
```
---


"""
Script that sends POST request to app and prints the responses.
This is easy to pretty print the results and testing.
"""
import argparse
import requests

DEFAULT_URL = "http://127.0.0.1:8000/query"


def send_query(question, session_id, url=DEFAULT_URL, timeout=180):
    headers = {"Content-Type": "application/json"}
    payload = {"session_id": session_id, "question": question, "message_type": "human"}
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    try:
        response_data = response.json()
    except ValueError:
        response_data = None

    return {
        "status_code": response.status_code,
        "ok": response.ok,
        "payload": payload,
        "response": response,
        "json": response_data,
        "text": response.text,
    }


def run_query(question, session_id, url=DEFAULT_URL):
    try:
        result = send_query(question, session_id, url=url)
        response_data = result["json"] or {}

        print(result["payload"])
        print("Response:")
        print(response_data.get("response", "No response returned"))
        print("SQL query:")
        print(response_data.get("sql_query", "No SQL query returned"))
        print("Table:")
        print(response_data.get("query_results", "No query result returned"))
        print("Profiling:")
        print(response_data.get("profiling", "No profiling payload returned"))
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", help="User question", type=str)
    parser.add_argument("--session_id", help="session id", type=int)
    parser.add_argument("--url", help="query endpoint URL", type=str, default=DEFAULT_URL)
    args = parser.parse_args()
    # question = "For each area in New York, give count of each crime type."
    # question = "Give me number of employees who are male"
    # question = "Retrieve all records from the economic_income_and_benefits table where the mean_household_income is more than 100,000 and the crime classification (Crime_Class) is 'Felony'."
    run_query(args.question, args.session_id, url=args.url)

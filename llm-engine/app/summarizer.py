from langgraph.graph import StateGraph
from typing import List, Dict
from langchain.schema import HumanMessage

def summarize_chat_history(history: List[Dict[str, str]], llm) -> Dict[str, str]:
    def summarize(state):
        """Summarization logic"""
        summary_prompt = f"""
        Summarize the following conversation, ensuring clarity, conciseness, and completeness:
        - **SQL Queries:** Retain only **the last 3 unique queries** (if modified, store only the **final version**).
        - **User Intent:** Summarize the key **questions or requests** made by the user.
        - **Query Evolution:** Capture any **modifications, corrections, or refinements** in query logic.
        - **Schema Updates:** If the user modified a table (added columns, constraints, etc.), update schema info.
        - **Redundancy Removal:** Eliminate **repetitive or unnecessary prompts**, keeping only **essential context**.
        - **Logical Grouping:** Group related **queries and their responses** to maintain a **coherent structure**.

        ### Conversation History:
        {state["history"]}

        ### Output Format:
        - **User Request(s):** <Summarized user intent>
        - **Final SQL Queries:**
        1. <SQL Query 1>
        2. <SQL Query 2>
        3. <SQL Query 3> (if applicable)
        - **Schema Changes (if any):** <Updated schema details>
        """

        response = llm.invoke([HumanMessage(content=summary_prompt)])
        return {"summary": response.content, "messages": state["history"][-2:]}

    workflow = StateGraph(dict)
    workflow.add_node("summarizer", summarize)
    workflow.set_entry_point("summarizer")

    app = workflow.compile()

    summarized_history = app.invoke({"history": history})
    
    print("debug:", summarized_history)
    return summarized_history

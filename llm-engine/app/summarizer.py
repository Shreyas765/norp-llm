from langgraph.graph import StateGraph
from typing import List, Dict
from langchain.schema import HumanMessage

def summarize_chat_history(history: List[Dict[str, str]], llm) -> Dict[str, str]:
    def summarize(state):
        """Summarization logic"""
        summary_prompt = f"""
        Summarize the following conversation while ensuring key details are retained:
        - Include Database schema information.
        - Capture all previously generated SQL queries.
        - Preserve the user's intent and any modifications they requested.
        - Ensure clarity and conciseness while maintaining essential details.
        - Remove redundant prompts to reduce the length of the history
        
        Conversation History:
        {state["history"]}
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

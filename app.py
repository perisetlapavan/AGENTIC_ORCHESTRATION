import os
import sys
import io
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_community.tools.tavily_search import TavilySearchResults


load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)

# Initialize the Tavily search tool (fetches top 3 relevant results)
web_search_tool = TavilySearchResults(max_results=3)

# --- 1. Expanded Shared State ---
class MarketGraphState(TypedDict):
    company_name: str
    competitors: List[str]
    research_notes: str
    generated_code: str
    chart_saved_at: str
    error_log: str
    current_step: str

# --- 2. Existing Research Node ---
# --- 2. Dynamic Research Node ---
def research_node(state: MarketGraphState):
    print("\n--- 🔍 Research Agent Active (with Web Browsing) ---")
    company = state["company_name"]
    
    # 1. Execute live web search
    search_query = f"major direct corporate competitors for {company} recent news market share"
    print(f"🌐 Browsing the web for: '{search_query}'...")
    
    try:
        search_results = web_search_tool.invoke({"query": search_query})
        # Format results into a readable string block for the LLM
        context = "\n".join([f"- {result['content']}" for result in search_results])
    except Exception as e:
        print(f"⚠️ Search failed: {e}. Falling back to LLM internal knowledge.")
        context = "No live search results available."

    # 2. Feed the live web data into the prompt
    prompt = f"""You are a market research expert. 
    Using the following real-time web search results as your context, identify 3 major direct corporate competitors for the company: {company}.
    
    Web Context:
    {context}
    
    Provide your response as a comma-separated list of just the names. 
    Example format: Competitor1, Competitor2, Competitor3
    Do not write any introductory or concluding text.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Clean and split the response into a clean Python list
    raw_competitors = response.content.strip()
    competitor_list = [c.strip() for c in raw_competitors.split(",") if c.strip()]
    
    # Fallback to defaults if the LLM output formatting fails
    if not competitor_list:
        competitor_list = ["Competitor A", "Competitor B", "Competitor C"]

    print(f"🎯 Found competitors for {company}: {competitor_list}")
    
    return {
        "research_notes": f"{company} operates in a highly competitive market against {', '.join(competitor_list)}. Context gathered:\n{context[:300]}...",
        "competitors": competitor_list,
        "current_step": "research_complete"
    }
# def research_node(state: MarketGraphState):
#     print("\n--- 🔍 Research Agent Active ---")
#     company = state["company_name"]
    
#     # Prompt the LLM to find the competitors dynamically
#     prompt = f"""You are a market research expert. 
#     Identify 3 major direct corporate competitors for the company: {company}.
    
#     Provide your response as a comma-separated list of just the names. 
#     Example format: Competitor1, Competitor2, Competitor3
#     Do not write any introductory or concluding text.
#     """
    
#     response = llm.invoke([HumanMessage(content=prompt)])
    
#     # Clean and split the response into a clean Python list
#     raw_competitors = response.content.strip()
#     competitor_list = [c.strip() for c in raw_competitors.split(",") if c.strip()]
    
#     # Fallback to defaults if the LLM output formatting fails
#     if not competitor_list:
#         competitor_list = ["Competitor A", "Competitor B", "Competitor C"]

#     print(f"🎯 Found competitors for {company}: {competitor_list}")
    
#     return {
#         "research_notes": f"{company} operates in a highly competitive market against {', '.join(competitor_list)}.",
#         "competitors": competitor_list,
#         "current_step": "research_complete"
#     }

# --- 3. New Coder Node ---
def coder_node(state: MarketGraphState):
    print("\n--- 💻 Coder Agent Generating Chart Code ---")
    company = state["company_name"]
    competitors = ", ".join(state["competitors"])
    error_context = f"Previous error to fix: {state.get('error_log')}" if state.get("error_log") else ""

    prompt = f"""You are an expert data visualization developer. 
    Write a pure Python script using `matplotlib` to create a mock market share horizontal bar chart comparing {company} with its competitors: {competitors}.
    
    Requirements:
    - Save the chart as 'market_chart.png' using `plt.savefig('market_chart.png')`.
    - Do NOT call `plt.show()`.
    - Output ONLY valid executable Python code block inside standard markdown formatting. No conversational filler text.
    
    {error_context}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Extract code from markdown blocks securely
    raw_content = response.content
    code = raw_content.split("```python")[-1].split("```")[0].strip() if "```python" in raw_content else raw_content
    
    return {"generated_code": code, "current_step": "code_generated"}

# --- 4. New Code Executor Node (Self-Correction Loop) ---
def executor_node(state: MarketGraphState):
    print("\n--- ⚙️ Executor Node Running Code ---")
    code_to_run = state["generated_code"]
    
    # Redirect standard output and intercept execution errors safely
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        # Warning: exec() is used here for local MVP testing. 
        # In a production environment, isolate this inside a Docker sandbox or use a WASM runtime.
        local_vars = {}
        exec(code_to_run, globals(), local_vars)
        sys.stdout = old_stdout
        print("✅ Chart generated successfully saved to disk!")
        return {"chart_saved_at": "market_chart.png", "error_log": "", "current_step": "execution_success"}
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"❌ Execution failed: {str(e)}")
        return {"error_log": str(e), "current_step": "execution_failed"}

# --- 5. Advanced Supervisor Router Logic ---
def supervisor_router(state: MarketGraphState):
    print("\n--- 🎛️ Supervisor Evaluating State ---")
    
    if not state.get("research_notes"):
        return "go_to_research"
    
    if state.get("current_step") == "research_complete":
        return "go_to_coder"
        
    if state.get("current_step") == "code_generated":
        return "go_to_executor"
        
    if state.get("current_step") == "execution_failed":
        print("🔄 Routing back to Coder to fix syntax/runtime bugs...")
        return "go_to_coder" # Loops back to Coder with the error trace!
        
    return "go_to_end"

# --- 6. Build the Graph ---
workflow = StateGraph(MarketGraphState)

workflow.add_node("researcher", research_node)
workflow.add_node("coder", coder_node)
workflow.add_node("executor", executor_node)

# Connect everything dynamically via the Supervisor
workflow.add_conditional_edges(START, supervisor_router, {
    "go_to_research": "researcher",
    "go_to_coder": "coder",
    "go_to_executor": "executor",
    "go_to_end": END
})

for node in ["researcher", "coder", "executor"]:
    workflow.add_conditional_edges(node, supervisor_router, {
        "go_to_research": "researcher",
        "go_to_coder": "coder",
        "go_to_executor": "executor",
        "go_to_end": END
    })

app = workflow.compile()

if __name__ == "__main__":
    initial_input = {
        "company_name": "Tesla",
        "competitors": [],
        "research_notes": "",
        "generated_code": "",
        "chart_saved_at": "",
        "error_log": "",
        "current_step": "start"
    }
    
    final_state = app.invoke(initial_input)
    print(f"\n🎉 Workflow Finished. Chart Location: {final_state.get('chart_saved_at')}")
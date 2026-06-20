import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware # 1. Import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

# Import your compiled graph from app.py
from app import app as agent_graph

app = FastAPI(
    title="Agentic Market Intelligence API",
    description="A production-ready API that orchestrates research, code generation, and chart execution loops.",
    version="1.0.0"
)

# --- 1. Define Request & Response Schemas ---
class ChartRequest(BaseModel):
    company_name: str = Field(..., example="Tesla", description="The target company to analyze.")

class ChartResponse(BaseModel):
    company_name: str
    competitors: List[str]
    chart_url: str
    execution_status: str
    error_log: str = ""

# --- 2. Add CORS policies allowing communication from web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allows all origins. Change to exact frontend port in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Endpoint to Trigger the Agent Graph ---
@app.post("/api/v1/generate-chart", response_model=ChartResponse)
async def generate_market_chart(request: ChartRequest):
    # Initialize the graph state with incoming request data
    initial_state = {
        "company_name": request.company_name,
        "competitors": [],
        "research_notes": "",
        "generated_code": "",
        "chart_saved_at": "",
        "error_log": "",
        "current_step": "start"
    }
    
    try:
        # Run the LangGraph workflow synchronously inside the endpoint
        # (For highly scalable production, run this in a background thread or celery worker)
        final_state = agent_graph.invoke(initial_state)
        
        # Check if the execution loop repeatedly failed
        if final_state.get("current_step") == "execution_failed":
            raise HTTPException(
                status_code=500, 
                detail=f"Agent loop failed to generate a valid chart. Error: {final_state.get('error_log')}"
            )
            
        return ChartResponse(
            company_name=final_state["company_name"],
            competitors=final_state["competitors"],
            chart_url=f"/api/v1/charts/{final_state['chart_saved_at']}",
            execution_status=final_state["current_step"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# --- 4. Endpoint to Serve the Generated Image File ---
@app.get("/api/v1/charts/{filename}")
async def get_generated_chart(filename: str):
    file_path = os.path.join(os.getcwd(), filename)
    
    # Ensure security constraint: check that the file exists locally
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested chart image not found.")
        
    return FileResponse(file_path, media_type="image/png")
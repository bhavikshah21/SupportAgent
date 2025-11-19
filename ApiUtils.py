
# ============================================================================
# 5. FASTAPI APPLICATION
# ============================================================================

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(title="Agentic AI Support System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = load_config()
data_layer = DataAccessLayer(config)
llm_client = LLMClient(config['anthropic_api_key'])
tools = ToolRegistry(data_layer)
orchestrator = AgentOrchestrator(llm_client, data_layer, tools)

@app.post("/api/v1/detect-issues")
async def detect_issues(request: AgentRequest):
    """Endpoint to detect production issues"""
    result = await orchestrator.execute(
        AgentRequest(
            mode=AgentMode.ISSUE_DETECTION,
            system=request.system,
            date=request.date
        )
    )
    return result

@app.post("/api/v1/diagnose")
async def diagnose_issues(request: AgentRequest):
    """Endpoint for full diagnosis (detect + diagnose)"""
    result = await orchestrator.execute(
        AgentRequest(
            mode=AgentMode.FULL_DIAGNOSIS,
            system=request.system,
            date=request.date
        )
    )
    return result

@app.post("/api/v1/query")
async def custom_query(query: str, system: str):
    """Flexible endpoint for custom queries"""
    result = await orchestrator.execute(
        AgentRequest(
            mode=AgentMode.CUSTOM_QUERY,
            system=system,
            specific_query=query
        )
    )
    return result

@app.get("/api/v1/logs/{system}/{date}")
async def get_logs(system: str, date: str):
    """API to retrieve log data"""
    log_date = datetime.strptime(date, '%Y-%m-%d')
    return await data_layer.get_log_summary(system, log_date)

@app.get("/api/v1/compare-data/{system}/{table}")
async def compare_data(
    system: str, 
    table: str, 
    date1: str, 
    date2: str
):
    """API to compare database data between dates"""
    d1 = datetime.strptime(date1, '%Y-%m-%d')
    d2 = datetime.strptime(date2, '%Y-%m-%d')
    
    return await data_layer.compare_database_data(
        system, table, d1, d2, 
        key_columns=['id', 'amount', 'status']
    )


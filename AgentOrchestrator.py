from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta

class AgentMode(Enum):
    ISSUE_DETECTION = "issue_detection"
    FULL_DIAGNOSIS = "full_diagnosis"
    CUSTOM_QUERY = "custom_query"

class AgentRequest(BaseModel):
    mode: AgentMode
    system: str  # "risk_management" or "pnl_system"
    date: Optional[datetime] = None
    specific_query: Optional[str] = None

class AgentOrchestrator:
    """
    Main orchestrator that routes requests to appropriate agents
    and coordinates multi-step workflows
    """
    
    def __init__(self, llm_client, data_layer, tools):
        self.llm_client = llm_client
        self.data_layer = data_layer
        self.tools = tools
        self.context_memory = {}
    
    async def execute(self, request: AgentRequest) -> Dict:
        """Main execution flow"""
        
        if request.mode == AgentMode.ISSUE_DETECTION:
            return await self.detect_issues(request)
        
        elif request.mode == AgentMode.FULL_DIAGNOSIS:
            # Two-phase: detect then diagnose
            issues = await self.detect_issues(request)
            if issues['has_issues']:
                diagnosis = await self.diagnose_issues(request, issues)
                return {**issues, **diagnosis}
            return issues
        
        elif request.mode == AgentMode.CUSTOM_QUERY:
            return await self.handle_custom_query(request)
    
    async def detect_issues(self, request: AgentRequest) -> Dict:
        """Phase 1: Issue Detection Agent"""
        
        # Get today's and yesterday's data
        today = request.date or datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Parallel data collection
        tasks = [
            self.data_layer.get_log_summary(request.system, today),
            self.data_layer.get_log_summary(request.system, yesterday),
            self.data_layer.get_metrics(request.system, today),
            self.data_layer.get_metrics(request.system, yesterday)
        ]
        
        log_today, log_yesterday, metrics_today, metrics_yesterday = await asyncio.gather(*tasks)
        
        # Build prompt for LLM
        analysis_prompt = self._build_detection_prompt(
            log_today, log_yesterday, 
            metrics_today, metrics_yesterday
        )
        
        # LLM analyzes for anomalies
        llm_response = await self.llm_client.analyze(
            prompt=analysis_prompt,
            tools=self.tools.get_detection_tools()
        )
        
        return self._parse_detection_response(llm_response)
    
    async def diagnose_issues(self, request: AgentRequest, issues: Dict) -> Dict:
        """Phase 2: Diagnostic Agent"""
        
        # Agent decides what data to fetch based on detected issues
        diagnostic_plan = await self._create_diagnostic_plan(issues)
        
        # Execute diagnostic steps
        diagnostic_data = await self._execute_diagnostic_plan(
            diagnostic_plan, 
            request.system
        )
        
        # LLM performs root cause analysis
        diagnosis_prompt = self._build_diagnosis_prompt(
            issues, 
            diagnostic_data
        )
        
        diagnosis = await self.llm_client.analyze(
            prompt=diagnosis_prompt,
            tools=self.tools.get_diagnosis_tools()
        )
        
        return self._parse_diagnosis_response(diagnosis)




# ============================================================================
# 6. TOOL REGISTRY FOR LLM
# ============================================================================

class ToolRegistry:
    """
    Defines tools that LLM can call to gather more information
    """
    
    def __init__(self, data_layer: DataAccessLayer):
        self.data_layer = data_layer
    
    def get_detection_tools(self) -> List[Dict]:
        """Tools available during issue detection phase"""
        return [
            {
                "name": "get_error_details",
                "description": "Retrieve detailed error messages from logs",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "system": {"type": "string"},
                        "date": {"type": "string"},
                        "error_type": {"type": "string"}
                    }
                }
            },
            {
                "name": "compare_metrics",
                "description": "Compare system metrics between two dates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "system": {"type": "string"},
                        "metric_name": {"type": "string"},
                        "date1": {"type": "string"},
                        "date2": {"type": "string"}
                    }
                }
            }
        ]
    
    def get_diagnosis_tools(self) -> List[Dict]:
        """Tools available during diagnosis phase"""
        return [
            {
                "name": "check_database_consistency",
                "description": "Verify data consistency in database tables",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "date": {"type": "string"}
                    }
                }
            },
            {
                "name": "fetch_upstream_data",
                "description": "Get data from upstream systems",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source_system": {"type": "string"},
                        "date": {"type": "string"}
                    }
                }
            }
        ]


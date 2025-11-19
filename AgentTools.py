
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


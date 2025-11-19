# ============================================================================
# 2. DATA ACCESS LAYER - APIs for Data Retrieval
# ============================================================================

class DataAccessLayer:
    """
    Unified interface for accessing logs, databases, and external systems
    """
    
    def __init__(self, config: Dict):
        self.log_reader = LogReader(config['log_paths'])
        self.db_client = DatabaseClient(config['db_config'])
        self.external_systems = ExternalSystemsClient(config['external_apis'])
    
    async def get_log_summary(self, system: str, date: datetime) -> Dict:
        """Extract and summarize logs for a specific date"""
        log_file = self.log_reader.get_log_file(system, date)
        
        # Parse logs for errors, warnings, key metrics
        parsed_logs = await self.log_reader.parse_logs(log_file)
        
        return {
            'error_count': parsed_logs['errors'],
            'warning_count': parsed_logs['warnings'],
            'critical_events': parsed_logs['critical'],
            'performance_metrics': parsed_logs['metrics'],
            'sample_errors': parsed_logs['error_samples'][:10]
        }
    
    async def get_metrics(self, system: str, date: datetime) -> Dict:
        """Get system metrics from database"""
        query = """
            SELECT 
                run_status,
                record_count,
                processing_time,
                data_volume,
                error_rate
            FROM system_metrics
            WHERE system_name = %s 
            AND run_date = %s
        """
        
        return await self.db_client.execute(query, (system, date))
    
    async def compare_database_data(
        self, 
        system: str, 
        table: str, 
        date1: datetime, 
        date2: datetime,
        key_columns: List[str]
    ) -> Dict:
        """Compare database records between two dates"""
        
        # Build dynamic comparison query
        query = f"""
            WITH day1 AS (
                SELECT {', '.join(key_columns)}
                FROM {table}
                WHERE business_date = %s
            ),
            day2 AS (
                SELECT {', '.join(key_columns)}
                FROM {table}
                WHERE business_date = %s
            )
            SELECT 
                COUNT(CASE WHEN day1.id IS NULL THEN 1 END) as missing_in_day1,
                COUNT(CASE WHEN day2.id IS NULL THEN 1 END) as missing_in_day2,
                COUNT(*) as total_records
            FROM day1
            FULL OUTER JOIN day2 ON day1.id = day2.id
        """
        
        return await self.db_client.execute(query, (date1, date2))
    
    async def get_upstream_data_diff(
        self, 
        source_system: str, 
        date1: datetime, 
        date2: datetime
    ) -> Dict:
        """Compare input data from external systems"""
        
        data1 = await self.external_systems.fetch_data(source_system, date1)
        data2 = await self.external_systems.fetch_data(source_system, date2)
        
        return self._calculate_diff(data1, data2)


"""
SQL Database Tool with AI-powered text-to-SQL capabilities.

Inspired by vanna.ai and other database AI integrations.
"""
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import re
import os
import httpx


class SQLDatabaseTool:
    """AI-powered SQL database query tool with schema awareness."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SQL database tool.
        
        Args:
            config: Tool configuration including databases, schema, and LLM settings
        """
        self.config = config
        self.databases = config.get('databases', {})
        self.llm_config = config.get('llm_config', {})
        self.read_only = config.get('read_only', True)
        self.max_rows = config.get('max_rows', 1000)
        self.allowed_operations = config.get('allowed_operations', ['SELECT'])
        self.blocked_keywords = [kw.upper() for kw in config.get('blocked_keywords', [])]
        
    def _get_connection(self, database_name: str = 'default') -> sqlite3.Connection:
        """Get database connection."""
        if database_name not in self.databases:
            raise ValueError(f"Database '{database_name}' not found in configuration")
        
        db_config = self.databases[database_name]
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = db_config.get('path', './data/databases/sample.db')
            # Expand environment variables
            db_path = os.path.expandvars(db_path)
            
            # If path is relative, resolve it relative to project root
            if not os.path.isabs(db_path):
                # Get project root (parent of tools directory)
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(project_root, db_path)
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            raise NotImplementedError(f"Database type '{db_type}' not yet implemented")
    
    def _validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        sql_upper = sql.upper().strip()
        
        # Check for blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in sql_upper:
                return False, f"Blocked keyword '{keyword}' found in query"
        
        # Check allowed operations
        if self.read_only:
            found_allowed = False
            for op in self.allowed_operations:
                if sql_upper.startswith(op.upper()):
                    found_allowed = True
                    break
            
            if not found_allowed:
                return False, f"Only {', '.join(self.allowed_operations)} operations are allowed"
        
        return True, None
    
    def _get_schema_context(self, database_name: str = 'default') -> str:
        """Get schema information as context for LLM."""
        if database_name not in self.databases:
            return ""
        
        db_config = self.databases[database_name]
        schema = db_config.get('schema', {})
        tables = schema.get('tables', [])
        
        context_parts = [
            "Database Schema:",
            f"Database: {db_config.get('description', database_name)}",
            ""
        ]
        
        for table in tables:
            context_parts.append(f"Table: {table['name']}")
            context_parts.append(f"Description: {table.get('description', 'N/A')}")
            context_parts.append("Columns:")
            
            for col in table.get('columns', []):
                col_info = f"  - {col['name']} ({col['type']})"
                if col.get('primary_key'):
                    col_info += " [PRIMARY KEY]"
                if col.get('foreign_key'):
                    col_info += f" [FOREIGN KEY -> {col['foreign_key']}]"
                col_info += f": {col.get('description', 'N/A')}"
                context_parts.append(col_info)
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _get_sample_queries_context(self, database_name: str = 'default') -> str:
        """Get sample queries as context for LLM."""
        if database_name not in self.databases:
            return ""
        
        db_config = self.databases[database_name]
        sample_queries = db_config.get('sample_queries', [])
        
        if not sample_queries:
            return ""
        
        context_parts = [
            "Sample Queries (for reference):",
            ""
        ]
        
        for i, sample in enumerate(sample_queries, 1):
            context_parts.append(f"{i}. Purpose: {sample.get('purpose', 'N/A')}")
            context_parts.append(f"   Question: {sample.get('question', 'N/A')}")
            context_parts.append(f"   SQL: {sample.get('sql', 'N/A').strip()}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def _generate_sql_from_natural_language(
        self, 
        question: str, 
        database_name: str = 'default'
    ) -> str:
        """
        Generate SQL from natural language using LLM.
        
        Args:
            question: Natural language question
            database_name: Database to query
            
        Returns:
            Generated SQL query
        """
        schema_context = self._get_schema_context(database_name)
        samples_context = self._get_sample_queries_context(database_name)
        
        prompt = f"""You are a SQL expert. Convert the natural language question into a SQL query.

{schema_context}

{samples_context}

Rules:
1. Generate ONLY the SQL query, no explanations
2. Use only SELECT statements (read-only)
3. Use proper JOIN syntax when needed
4. Include appropriate WHERE, GROUP BY, ORDER BY clauses
5. Limit results appropriately
6. Return ONLY valid SQL, nothing else

Question: {question}

SQL Query:"""

        # Call LLM
        provider = self.llm_config.get('provider', 'openai_compatible')
        endpoint = self.llm_config.get('endpoint', '')
        model = self.llm_config.get('model', 'gpt-3.5-turbo')
        api_key = self.llm_config.get('api_key', '')
        
        if not endpoint:
            raise ValueError("LLM endpoint not configured")
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a SQL expert. Generate only valid SQL queries.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': self.llm_config.get('temperature', 0.1),
            'max_tokens': self.llm_config.get('max_tokens', 500)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{endpoint}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        # Extract SQL from response
        sql = result['choices'][0]['message']['content'].strip()
        
        # Clean up the SQL (remove markdown code blocks if present)
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = sql.strip()
        
        return sql
    
    def _execute_sql(
        self, 
        sql: str, 
        database_name: str = 'default',
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Execute SQL query and return results.
        
        Returns:
            Tuple of (results, execution_time)
        """
        start_time = time.time()
        
        # Add LIMIT if not present and limit is specified
        sql_upper = sql.upper().strip()
        if 'LIMIT' not in sql_upper and limit:
            sql = f"{sql.rstrip(';')} LIMIT {min(limit, self.max_rows)}"
        
        conn = self._get_connection(database_name)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(row))
            
            execution_time = time.time() - start_time
            return results, execution_time
            
        finally:
            conn.close()
    
    def _get_schema_info(self, database_name: str = 'default') -> Dict[str, Any]:
        """Get schema information for the database."""
        if database_name not in self.databases:
            return {'error': f"Database '{database_name}' not found"}
        
        db_config = self.databases[database_name]
        schema = db_config.get('schema', {})
        
        return {
            'database': database_name,
            'description': db_config.get('description', ''),
            'type': db_config.get('type', 'sqlite'),
            'tables': schema.get('tables', []),
            'sample_queries': db_config.get('sample_queries', [])
        }


async def query_database(
    question: str,
    mode: str = 'natural',
    database_name: str = 'default',
    limit: int = 100,
    **kwargs
) -> Dict[str, Any]:
    """
    Query database using natural language or SQL.
    
    Args:
        question: Natural language question or SQL query
        mode: Query mode ('natural', 'sql', or 'schema')
        database_name: Database connection name
        limit: Maximum rows to return
        **kwargs: Additional arguments including tool config
        
    Returns:
        Query results with metadata
    """
    try:
        # Get tool config from kwargs
        tool_config = kwargs.get('tool_config', {})
        implementation = tool_config.get('implementation', {})
        
        # Initialize tool
        tool = SQLDatabaseTool(implementation)
        
        # Handle different modes
        if mode == 'schema':
            schema_info = tool._get_schema_info(database_name)
            return {
                'success': True,
                'mode': 'schema',
                'schema': schema_info
            }
        
        # Generate or use SQL
        if mode == 'natural':
            # Text-to-SQL conversion
            generated_sql = await tool._generate_sql_from_natural_language(
                question, 
                database_name
            )
        else:
            # Direct SQL mode
            generated_sql = question
        
        # Validate SQL
        is_valid, error_msg = tool._validate_sql(generated_sql)
        if not is_valid:
            return {
                'success': False,
                'mode': mode,
                'question': question,
                'generated_sql': generated_sql,
                'error': f"SQL validation failed: {error_msg}"
            }
        
        # Execute SQL
        results, execution_time = tool._execute_sql(
            generated_sql,
            database_name,
            limit
        )
        
        return {
            'success': True,
            'mode': mode,
            'question': question,
            'generated_sql': generated_sql,
            'results': results,
            'row_count': len(results),
            'execution_time': round(execution_time, 3),
            'database': database_name
        }
        
    except Exception as e:
        return {
            'success': False,
            'mode': mode,
            'question': question,
            'error': str(e)
        }

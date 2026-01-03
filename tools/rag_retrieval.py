"""
RAG Document Retrieval Tool

Retrieves relevant document chunks from RAG system using semantic search.
Connects to dsp-rag or compatible RAG services.
"""
import os
import json
from typing import Dict, Any, List, Optional
import httpx
import asyncio


class RAGRetrievalTool:
    """RAG document retrieval tool for semantic search."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RAG retrieval tool.
        
        Args:
            config: Tool configuration including endpoint and settings
        """
        self.config = config
        self.endpoint = config.get('endpoint', 'http://localhost:8000/retrieve')
        self.timeout = config.get('timeout', 30)
        self.retry_count = config.get('retry_count', 2)
        self.retry_delay = config.get('retry_delay', 1)
        self.rag_configs = config.get('rag_configs', {})
        
    def _get_endpoint_for_config(self, configuration_name: str) -> str:
        """
        Get the appropriate endpoint for a configuration.
        
        Args:
            configuration_name: RAG configuration name
            
        Returns:
            Full endpoint URL
        """
        # Check if there's a specific config
        if configuration_name in self.rag_configs:
            config = self.rag_configs[configuration_name]
            base_endpoint = config.get('endpoint', self.endpoint.rsplit('/', 1)[0])
            return f"{base_endpoint}/retrieve"
        
        # Use default endpoint
        return self.endpoint
    
    def _prepare_request_body(
        self,
        query: str,
        configuration_name: str = 'default',
        top_k: int = 5,
        use_reranking: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Prepare the request body for RAG retrieval.
        
        Args:
            query: Search query
            configuration_name: RAG configuration name
            top_k: Number of results
            use_reranking: Whether to rerank
            metadata_filter: Metadata filters
            min_score: Minimum score threshold
            
        Returns:
            Request body dictionary
        """
        body = {
            "query": query,
            "configuration_name": configuration_name,
            "top_k": top_k,
            "use_reranking": use_reranking
        }
        
        if metadata_filter:
            body["metadata_filter"] = metadata_filter
        
        if min_score > 0.0:
            body["min_score"] = min_score
        
        return body
    
    def _parse_response(
        self,
        response_data: Dict[str, Any],
        query: str,
        configuration_name: str
    ) -> Dict[str, Any]:
        """
        Parse RAG service response.
        
        Args:
            response_data: Raw response from RAG service
            query: Original query
            configuration_name: Configuration used
            
        Returns:
            Parsed response dictionary
        """
        # Handle different response formats
        chunks = []
        
        # Check for documents in response
        if 'documents' in response_data:
            documents = response_data['documents']
        elif 'results' in response_data:
            documents = response_data['results']
        elif 'chunks' in response_data:
            documents = response_data['chunks']
        else:
            documents = []
        
        # Normalize chunk format
        for doc in documents:
            chunk = {
                'content': doc.get('content') or doc.get('text') or doc.get('page_content', ''),
                'metadata': doc.get('metadata', {}),
                'score': doc.get('score') or doc.get('similarity_score', 0.0)
            }
            chunks.append(chunk)
        
        return {
            'success': True,
            'query': query,
            'configuration_name': configuration_name,
            'chunks': chunks,
            'total_chunks': len(chunks)
        }
    
    async def retrieve(
        self,
        query: str,
        configuration_name: str = 'default',
        top_k: int = 5,
        use_reranking: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Retrieve relevant document chunks from RAG system.
        
        Args:
            query: Search query
            configuration_name: RAG configuration name
            top_k: Number of results to return
            use_reranking: Whether to use reranking
            metadata_filter: Filter by metadata
            min_score: Minimum similarity score
            
        Returns:
            Retrieval results with chunks
        """
        endpoint = self._get_endpoint_for_config(configuration_name)
        body = self._prepare_request_body(
            query, configuration_name, top_k, use_reranking, metadata_filter, min_score
        )
        
        # Get headers from config
        headers = self.config.get('headers', {})
        
        # Resolve environment variables in headers
        resolved_headers = {}
        for key, value in headers.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                resolved_headers[key] = os.getenv(env_var, value)
            else:
                resolved_headers[key] = value
        
        # Retry logic
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        json=body,
                        headers=resolved_headers
                    )
                    response.raise_for_status()
                    
                    response_data = response.json()
                    return self._parse_response(response_data, query, configuration_name)
                    
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
            except httpx.RequestError as e:
                last_error = f"Request error: {str(e)}"
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        # All retries failed
        return {
            'success': False,
            'query': query,
            'configuration_name': configuration_name,
            'chunks': [],
            'total_chunks': 0,
            'error': last_error
        }


async def retrieve_documents(
    query: str,
    configuration_name: str = 'default',
    top_k: int = 5,
    use_reranking: bool = True,
    metadata_filter: Optional[Dict[str, Any]] = None,
    min_score: float = 0.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Retrieve relevant document chunks from RAG system.
    
    This is the main entry point called by the ADK tool system.
    
    Args:
        query: Search query or question
        configuration_name: RAG configuration/collection name
        top_k: Number of chunks to retrieve
        use_reranking: Whether to rerank results
        metadata_filter: Filter documents by metadata
        min_score: Minimum similarity score threshold
        **kwargs: Additional arguments including tool config
        
    Returns:
        Retrieval results with document chunks
    """
    try:
        # Get tool config from kwargs
        tool_config = kwargs.get('tool_config', {})
        implementation = tool_config.get('implementation', {})
        
        # Initialize tool
        tool = RAGRetrievalTool(implementation)
        
        # Retrieve documents
        result = await tool.retrieve(
            query=query,
            configuration_name=configuration_name,
            top_k=top_k,
            use_reranking=use_reranking,
            metadata_filter=metadata_filter,
            min_score=min_score
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'query': query,
            'configuration_name': configuration_name,
            'chunks': [],
            'total_chunks': 0,
            'error': str(e)
        }

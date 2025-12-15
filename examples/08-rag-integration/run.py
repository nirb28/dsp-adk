"""
Example 08: RAG Integration

This example demonstrates Retrieval-Augmented Generation (RAG)
using vector search for knowledge-grounded responses.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the RAG integration example."""
    print("=" * 60)
    print("Example 08: RAG Integration")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. RAG Architecture
        print("\n1. RAG Architecture:")
        print("""
   ┌─────────────────────────────────────────────────────────────┐
   │              Retrieval-Augmented Generation                 │
   └─────────────────────────────────────────────────────────────┘
   
   ┌──────────────────────────────────────────────────────────┐
   │                     OFFLINE                              │
   │  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
   │  │Documents │───▶│Embeddings│───▶│  Vector Store    │   │
   │  │ (PDFs,   │    │ Model    │    │  (FAISS/Redis/   │   │
   │  │  docs)   │    │          │    │   Elasticsearch) │   │
   │  └──────────┘    └──────────┘    └──────────────────┘   │
   └──────────────────────────────────────────────────────────┘
   
   ┌──────────────────────────────────────────────────────────┐
   │                     ONLINE                               │
   │                                                          │
   │  User Query                                              │
   │      │                                                   │
   │      ▼                                                   │
   │  ┌──────────┐    ┌──────────────────┐                   │
   │  │Embeddings│───▶│  Vector Search   │                   │
   │  │ Model    │    │  (top-k docs)    │                   │
   │  └──────────┘    └────────┬─────────┘                   │
   │                           │                              │
   │                           ▼                              │
   │               ┌───────────────────────┐                 │
   │               │    LLM Generation     │                 │
   │               │  (with retrieved      │                 │
   │               │   context)            │                 │
   │               └───────────┬───────────┘                 │
   │                           │                              │
   │                           ▼                              │
   │                    Final Response                        │
   │                   (with citations)                       │
   └──────────────────────────────────────────────────────────┘
""")
        
        # 2. Check tools
        print("2. Required Components:")
        
        response = await client.get("/tools/vector-search")
        if response.status_code == 200:
            tool = response.json()
            print(f"   ✓ vector-search tool: {tool['description'][:40]}...")
        
        response = await client.get("/agents/research-agent")
        if response.status_code == 200:
            agent = response.json()
            print(f"   ✓ research-agent: {agent['description'][:40]}...")
        
        # 3. Configuration
        print("\n3. Vector Search Configuration:")
        print("""
   vector-search tool:
     vector_store: faiss
     embedding_model: text-embedding-3-small
     connection_config:
       index_path: ./data/index
     
   Search parameters:
     top_k: 5          # Retrieve top 5 most similar
     threshold: 0.7    # Minimum similarity score
     filter:           # Optional metadata filtering
       category: "policy"
       department: "HR"
""")
        
        # 4. Example flow
        print("4. Example RAG Flow:")
        print("""
   User: "What does our policy say about remote work?"
   
   Step 1: Embed Query
   ─────────────────────
   Query → Embedding Model → [0.12, -0.34, 0.56, ...]
   
   Step 2: Vector Search
   ─────────────────────
   Search index for similar document embeddings
   
   Retrieved Documents:
   ┌────────────────────────────────────────────────────────┐
   │ Doc 1: HR_Policy_2024.pdf (score: 0.92)               │
   │ "Remote work is permitted for eligible employees..."   │
   ├────────────────────────────────────────────────────────┤
   │ Doc 2: Employee_Handbook.pdf (score: 0.85)            │
   │ "Work from home arrangements must be approved..."      │
   ├────────────────────────────────────────────────────────┤
   │ Doc 3: IT_Guidelines.pdf (score: 0.78)                │
   │ "Remote access requires VPN connection..."             │
   └────────────────────────────────────────────────────────┘
   
   Step 3: Generate Response
   ─────────────────────────
   research-agent receives:
   - Original query
   - Retrieved document chunks
   - Instruction to cite sources
   
   Step 4: Final Response
   ─────────────────────
   "According to our company policy, remote work is permitted
   for eligible employees who meet the following criteria:
   
   1. Must be in good standing (HR_Policy_2024.pdf, p.12)
   2. Role must be classified as remote-eligible
   3. Manager approval required (Employee_Handbook.pdf, p.45)
   
   Additionally, IT requirements include:
   - VPN connection for all remote access (IT_Guidelines.pdf)
   - Company-issued device recommended
   
   Sources:
   [1] HR_Policy_2024.pdf, Section 4.2
   [2] Employee_Handbook.pdf, Chapter 8
   [3] IT_Guidelines.pdf, Remote Access"
""")
        
        # 5. Advanced features
        print("5. Advanced RAG Features:")
        print("""
   Metadata Filtering:
     filter: {"department": "Engineering", "year": 2024}
   
   Hybrid Search:
     Combine vector search with keyword search
   
   Reranking:
     Use cross-encoder for better relevance ranking
   
   Query Expansion:
     Generate multiple query variations for better recall
""")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

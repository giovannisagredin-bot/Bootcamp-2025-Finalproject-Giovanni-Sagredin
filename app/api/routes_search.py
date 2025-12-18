"""
API endpoints for semantic search on scout reports
"""

import logging
from fastapi import APIRouter, HTTPException
from app.core.database import MongoDB
from app.vectorstore.manager import VectorStoreManager
from app.agents.search_agent import SearchAgent
from src.llm.utils import GenerativeAIClientFactory, Provider
from app.models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchSource
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search on scout reports using RAG
    
    Flow:
    1. Vector similarity search in ChromaDB
    2. Fetch full report details from MongoDB
    3. Generate answer with LLM based on context
    
    """
    try:
        logger.info(f"Semantic search: '{request.query}' (provider: {request.provider}, top_k: {request.top_k})")
        
        db = MongoDB.get_database()
        
        # Initialize components
        vector_store = VectorStoreManager()
        llm_client = GenerativeAIClientFactory.create_client(provider=Provider(request.provider))
        search_agent = SearchAgent(
            vector_store=vector_store,
            llm_client=llm_client,
            db=db,
            top_k=request.top_k
        )
        
        # Perform RAG search
        result = search_agent.search(request.query)
        
        # Convert sources to Pydantic models
        sources = [SemanticSearchSource(**source) for source in result['sources']]
        
        return SemanticSearchResponse(
            query=result['query'],
            answer=result['answer'],
            sources=sources,
            provider_used=request.provider
        )
        
    except Exception as e:
        logger.error(f"Semantic search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

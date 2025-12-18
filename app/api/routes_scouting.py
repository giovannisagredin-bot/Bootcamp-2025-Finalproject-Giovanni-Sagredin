"""
API endpoints for scouting reports
"""

import logging
from fastapi import APIRouter, HTTPException
from app.core.database import MongoDB
from app.pipeline.etl import ScoutReportPipeline
from app.pipeline.toxicity import ToxicityAnalyzer
from app.pipeline.exceptions import ToxicReportError
from src.llm.utils import GenerativeAIClientFactory, Provider
from app.models.schemas import (
    SubmitReportRequest,
    SubmitReportResponse,
    PlayerAutocompleteResult,
    PlayerAutocompleteResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scouting"])


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/reports", response_model=SubmitReportResponse)
async def submit_report(request: SubmitReportRequest):
    """
    Submit a new scout report
    
    Flow:
    1. Validate toxicity (raises 400 if toxic)
    2. Fetch player data
    3. Standardize with LLM
    4. Save to MongoDB (or mock in DEMO_MODE)
    
    Provider can be specified in request body: "openai", "google", or "mock"
    Returns report_id and summary on success
    """
    try:
        logger.info(f"Received report for player: {request.player_id} (provider: {request.provider})")
        
        # Initialize components
        from app.vectorstore.manager import VectorStoreManager
        
        db = MongoDB.get_database()
        llm_client = GenerativeAIClientFactory.create_client(provider=Provider(request.provider))
        toxicity_analyzer = ToxicityAnalyzer(llm_client)
        vector_store = VectorStoreManager()
        
        # Create pipeline with vector store integration
        pipeline = ScoutReportPipeline(db, llm_client, toxicity_analyzer, vector_store)
        
        result = pipeline.process_report(
            report_text=request.report_text,
            player_id=request.player_id
        )
        
        # Add provider info to response
        result["provider_used"] = request.provider
        
        return SubmitReportResponse(**result)
        
    except ToxicReportError as e:
        logger.warning(f"Toxic report rejected: {e.reason}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "toxic_content",
                "toxicity_score": e.toxicity_score,
                "reason": e.reason,
                "categories": e.categories,
                "suggestion": getattr(e, 'suggestion', None)
            }
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/players/search", response_model=PlayerAutocompleteResponse)
async def search_players(q: str):
    """
    Search players by name (autocomplete)
    
    Query parameter:
    - q: search query (minimum 2 chars)
    
    Returns list of matching players with id, name, position, nationality
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    try:
        # Search MongoDB
        db = MongoDB.get_database()
        # Case-insensitive regex search on name field (not full_name)

        players = db["final-project"].find(
            {"full_name": {"$regex": q, "$options": "i"}},
            {"_id": 1, "full_name": 1, "positions": 1, "nationality": 1, "overall_rating": 1}
        ).limit(10)

        results = [
            PlayerAutocompleteResult(
                id=str(p["_id"]),
                name=p.get("full_name", "Unknown"),
                position=p.get("positions", "Unknown"),
                nationality=p.get("nationality", "Unknown"),
                overall_rating=p.get("overall_rating", 0)
            )
            for p in players
        ]

        logger.info(f"Search '{q}' returned {len(results)} results")

        return PlayerAutocompleteResponse(
            results=results,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")

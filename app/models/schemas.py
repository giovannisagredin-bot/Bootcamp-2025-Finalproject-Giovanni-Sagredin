from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ToxicityAnalysis(BaseModel):
    """Result of toxicity analysis on a scout report"""
    is_toxic: bool = Field(description="Whether the report exceeds toxicity threshold")
    toxicity_score: float = Field(ge=0.0, le=1.0, description="Toxicity score from 0.0 (clean) to 1.0 (highly toxic)")
    categories: List[str] = Field(default_factory=list, description="Detected toxicity categories")
    reason: str = Field(description="Explanation of why the report was flagged or approved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_toxic": True,
                "toxicity_score": 0.85,
                "categories": ["identity_attack", "insult"],
                "reason": "Contains ethnic stereotypes and derogatory language"
            }
        }


class Player(BaseModel):
    """Player data from MongoDB"""
    player_id: Optional[str] = Field(None, alias="_id")
    name: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    position: Optional[str] = None
    overall_rating: Optional[int] = None
    
    class Config:
        populate_by_name = True


class ScoutReport(BaseModel):
    """Scout report submission"""
    player_id: str = Field(description="MongoDB player ID")
    report_text: str = Field(description="Raw scouting report text")
    scout_name: str = Field(description="Name of the scout")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlayerSearchQuery(BaseModel):
    """Search query for finding players"""
    query: str = Field(description="Natural language description of desired player profile")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to return")


class PlayerSearchResult(BaseModel):
    """Search result with player and report"""
    player: Player
    report_text: str
    similarity_score: float = Field(ge=0.0, le=1.0, description="Semantic similarity score")


# API Request/Response Models for Scouting


class SubmitReportRequest(BaseModel):
    """Request to submit a new scout report"""
    player_id: str = Field(..., description="Player ID from autocomplete selection")
    report_text: str = Field(..., min_length=10, description="Scout report text (minimum 10 chars)")
    provider: Literal["openai", "google", "mock"] = Field(default="openai", description="LLM provider to use")


class SubmitReportResponse(BaseModel):
    """Response after submitting a scout report"""
    status: str
    report_id: str
    player_name: str
    summary: str
    provider_used: str


class PlayerAutocompleteResult(BaseModel):
    """Single player result from autocomplete search"""
    id: str
    name: str
    position: str
    nationality: str
    overall_rating: int


class PlayerAutocompleteResponse(BaseModel):
    """Response with list of matching players for autocomplete"""
    results: List[PlayerAutocompleteResult]
    count: int


# Semantic Search Schemas

class SemanticSearchRequest(BaseModel):
    """Request for semantic search on scout reports"""
    query: str = Field(..., min_length=3, description="Search query (e.g., 'fast right-back good at crossing')")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to return")
    provider: Literal["openai", "google", "mock"] = Field(default="openai", description="LLM provider for answer generation")


class SemanticSearchSource(BaseModel):
    """Scout report source used for answer"""
    score: float = Field(description="Similarity score (lower = more similar)")
    report_id: str
    player_name: str
    player_position: str
    player_nationality: str
    overall_rating: Optional[int] = None
    potential: Optional[int] = None
    value_euro: Optional[int] = None
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    technical_skills: List[str]
    physical_attributes: List[str]


class SemanticSearchResponse(BaseModel):
    """Response from semantic search with RAG answer"""
    query: str
    answer: str = Field(description="LLM-generated answer based on scout reports")
    sources: List[SemanticSearchSource] = Field(description="Scout reports used to generate answer")
    provider_used: str

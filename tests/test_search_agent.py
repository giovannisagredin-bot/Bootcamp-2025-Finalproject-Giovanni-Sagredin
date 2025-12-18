"""Tests for Search Agent (RAG)"""
import pytest
from app.agents.search_agent import SearchAgent
from app.vectorstore.manager import VectorStoreManager
from src.llm.mock_client import MockClient
from unittest.mock import Mock, MagicMock
import tempfile
import shutil


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    from bson import ObjectId
    
    db = Mock()
    collection = MagicMock()
    
    # Mock MongoDB find_one to return sample report (with valid ObjectId)
    collection.find_one.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "player_name": "Fast Winger",
        "player_position": "Right Winger",
        "player_nationality": "Brazil",
        "overall_rating": 82,
        "potential": 88,
        "value_euro": 15000000,
        "summary": "Very fast winger with excellent dribbling",
        "strengths": ["Speed", "Dribbling", "Crossing"],
        "weaknesses": ["Defending", "Stamina"],
        "technical_skills": ["Ball Control", "Dribbling"],
        "physical_attributes": ["Pace", "Acceleration"]
    }
    
    db.__getitem__ = lambda self, key: collection
    return db


@pytest.fixture
def temp_vectorstore():
    """Create temporary vectorstore with test data"""
    temp_dir = tempfile.mkdtemp()
    manager = VectorStoreManager(persist_directory=temp_dir)
    
    # Add test documents (use valid MongoDB ObjectId format)
    documents = [
        {
            "report_id": "507f1f77bcf86cd799439011",  # Valid ObjectId format
            "player_name": "Fast Winger",
            "player_position": "Right Winger",
            "text_for_vectorization": "Very fast winger with excellent dribbling and pace. Good at crossing."
        }
    ]
    manager.add_documents(documents)
    
    yield manager
    
    # Cleanup with retry for Windows file locking
    try:
        import time
        time.sleep(0.1)  # Give ChromaDB time to close files
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass  # Ignore cleanup errors in tests


@pytest.fixture
def search_agent(temp_vectorstore, mock_db):
    """Create search agent with mock dependencies"""
    llm_client = MockClient()
    return SearchAgent(
        vector_store=temp_vectorstore,
        llm_client=llm_client,
        db=mock_db,
        top_k=3
    )


def test_search_agent_basic(search_agent):
    """Test basic RAG search functionality"""
    result = search_agent.search(query="fast winger with good dribbling")
    
    # Check structure
    assert "answer" in result
    assert "sources" in result
    assert "query" in result
    
    # Check query preserved
    assert result["query"] == "fast winger with good dribbling"
    
    # Check sources returned
    assert len(result["sources"]) > 0
    source = result["sources"][0]
    assert source["player_name"] == "Fast Winger"
    assert source["player_position"] == "Right Winger"


def test_search_preserves_metadata(search_agent):
    """Test that search preserves all metadata from MongoDB"""
    result = search_agent.search(query="fast player")
    
    source = result["sources"][0]
    
    # Check all metadata fields
    assert source["player_position"] == "Right Winger"
    assert source["player_nationality"] == "Brazil"
    assert source["overall_rating"] == 82
    assert source["potential"] == 88
    assert source["value_euro"] == 15000000
    
    # Check arrays
    assert "Speed" in source["strengths"]
    assert "Defending" in source["weaknesses"]
    assert "Ball Control" in source["technical_skills"]
    assert "Pace" in source["physical_attributes"]


def test_search_no_results(temp_vectorstore, mock_db):
    """Test search with no matching results (empty vector store)"""
    # Create agent with empty vectorstore
    temp_dir = tempfile.mkdtemp()
    empty_vectorstore = VectorStoreManager(persist_directory=temp_dir)
    
    agent = SearchAgent(
        vector_store=empty_vectorstore,
        llm_client=MockClient(),
        db=mock_db,
        top_k=3
    )
    
    result = agent.search(query="goalkeeper with shot stopping")
    
    # Should return empty sources and fallback message
    assert result["sources"] == []
    assert "No relevant scout reports found" in result["answer"]
    
    # Cleanup
    try:
        import time
        time.sleep(0.1)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass


def test_search_returns_top_k(search_agent):
    """Test that search respects top_k parameter"""
    # Agent initialized with top_k=3
    result = search_agent.search(query="winger")
    
    # Should return at most 3 results
    assert len(result["sources"]) <= 3


def test_llm_answer_generation(search_agent):
    """Test that LLM generates an answer"""
    result = search_agent.search(query="find fast player")
    
    # MockClient returns "Mock response for: {prompt}"
    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0

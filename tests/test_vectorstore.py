"""Tests for VectorStore Manager"""
import pytest
from app.vectorstore.manager import VectorStoreManager
import tempfile
import shutil
import time
import gc


@pytest.fixture
def temp_vectorstore():
    """Create temporary vectorstore for testing"""
    temp_dir = tempfile.mkdtemp()
    manager = VectorStoreManager(persist_directory=temp_dir)
    yield manager
    
    # Force cleanup of ChromaDB resources (Windows file locking)
    del manager
    gc.collect()
    time.sleep(0.2)
    
    # Cleanup temp directory with retry on Windows
    try:
        shutil.rmtree(temp_dir)
    except PermissionError:
        time.sleep(0.5)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_add_and_search_documents(temp_vectorstore):
    """Test adding documents and searching"""
    # Add test documents
    documents = [
        {
            "report_id": "test1",
            "player_name": "Cristiano Ronaldo",
            "player_position": "Forward",
            "summary": "Fast striker with excellent heading ability",
            "text_for_vectorization": "Fast striker with excellent heading ability and powerful shot"
        },
        {
            "report_id": "test2",
            "player_name": "Lionel Messi",
            "player_position": "Forward",
            "summary": "Technical dribbler with great vision",
            "text_for_vectorization": "Technical dribbler with great vision and passing accuracy"
        }
    ]
    
    temp_vectorstore.add_documents(documents)
    
    # Search for documents
    results = temp_vectorstore.similarity_search("fast striker", top_k=1)
    
    assert len(results) > 0
    assert results[0]["player_name"] == "Cristiano Ronaldo"


def test_empty_search(temp_vectorstore):
    """Test search on empty collection"""
    results = temp_vectorstore.similarity_search("test query")
    assert results == []


def test_add_documents_with_metadata(temp_vectorstore):
    """Test documents preserve metadata"""
    documents = [
        {
            "report_id": "meta_test",
            "player_name": "Test Player",
            "player_position": "Midfielder",
            "player_nationality": "Brazil",
            "overall_rating": 85,
            "summary": "Good midfielder",
            "text_for_vectorization": "Good midfielder with passing skills"
        }
    ]
    
    temp_vectorstore.add_documents(documents)
    results = temp_vectorstore.similarity_search("midfielder passing", top_k=1)
    
    assert len(results) > 0
    assert results[0]["player_nationality"] == "Brazil"
    assert results[0]["overall_rating"] == 85

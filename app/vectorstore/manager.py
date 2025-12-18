"""
Vector Store Manager using ChromaDB
Handles document embeddings and similarity search for scout reports
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from app.core.config import settings


logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages ChromaDB vector store for similarity search
    
    Features:
    - Creates embeddings automatically with ChromaDB
    - Stores embeddings + metadata together
    - Performs similarity search
    - Automatic persistence to disk
    a
    """
    
    def __init__(
        self, 
        persist_directory: str = "data/vectorstore",
        collection_name: str = "scout_reports"
    ):
        """
        Initialize Vector Store Manager with ChromaDB
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection (default: scout_reports)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client - use Cloud if credentials available, else local
        if settings.CHROMA_API_KEY and settings.CHROMA_TENANT and settings.CHROMA_DATABASE:
            logger.info(f"Initializing ChromaDB Cloud (tenant: {settings.CHROMA_TENANT})")
            self.client = chromadb.CloudClient(
                api_key=settings.CHROMA_API_KEY,
                tenant=settings.CHROMA_TENANT,
                database=settings.CHROMA_DATABASE
            )
        else:
            logger.info(f"Initializing ChromaDB Local (persist_dir: {persist_directory})")
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        # Get or create collection
        # ChromaDB uses sentence-transformers by default
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Football scout reports"}
        )
        
        logger.info(f"✓ Collection '{collection_name}' ready (count: {self.collection.count()})")
    
    def reset(self):
        """Reset/clear the entire collection """
        logger.warning(f"Resetting collection '{self.collection_name}'")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Football scout reports"}
        )
        logger.info("✓ Collection reset complete")
    
    def add_documents(self, documents: List[Dict]):
        """
        Add documents to vector store
        
        Args:
            documents: List of dicts with keys:
                - 'text': Text to embed (required)
                - 'report_id': MongoDB report ID (required - used as ChromaDB ID)
                - 'player_id': MongoDB player ID
                - 'player_name': Player name
                - (other metadata...)
        
        Example:
            documents = [
                {
                    'text': 'Player: Messi | Position: RW | Fast, excellent dribbling...',
                    'report_id': '507f1f77bcf86cd799439011',
                    'player_name': 'L. Messi',
                    'player_position': 'RW'
                }
            ]
        
        Note: ChromaDB automatically generates embeddings using sentence-transformers
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"⏳ Adding {len(documents)} documents to ChromaDB...")
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            # report_id is used as unique ID in ChromaDB
            report_id = doc.get('report_id')
            if not report_id:
                logger.error("Document missing 'report_id', skipping")
                continue
            
            ids.append(report_id)
            texts.append(doc.get('text', ''))
            
            # Extract metadata (everything except 'text')
            metadata = {k: v for k, v in doc.items() if k != 'text'}
            # ChromaDB metadata values must be strings, ints, floats, or bools
            # Convert None to empty string
            metadata = {k: (v if v is not None else "") for k, v in metadata.items()}
            metadatas.append(metadata)
        
        # Add to ChromaDB collection
        # ChromaDB will automatically generate embeddings
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"✓ Added {len(ids)} documents. Total: {self.collection.count()}")
    
    def similarity_search(
        self, 
        query: str, 
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform similarity search
        
        Args:
            query: Search query text (e.g., "Find fast right-back good at crossing")
            top_k: Number of results to return (default: 5)
            where: Optional metadata filter (e.g., {"player_position": "RB"})
            
        Returns:
            List of dicts with keys:
                - 'score': Similarity score (distance - lower = more similar)
                - 'report_id': MongoDB report ID
                - 'player_name': Player name
                - (other metadata...)
        
        Example:
            # Basic search
            results = manager.similarity_search("fast winger with good dribbling", top_k=3)
            
            # Search with filter
            results = manager.similarity_search(
                "good defender", 
                top_k=5,
                where={"player_nationality": "Spain"}
            )
        """
        if self.collection.count() == 0:
            logger.warning("Collection is empty, returning no results")
            return []
        
        logger.info(f"🔍 Searching for: '{query[:50]}...'")
        
        # Query ChromaDB
        # ChromaDB automatically generates query embedding and searches
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["metadatas", "distances"]
        )
        
        # Parse results
        output = []
        if results['ids'] and results['distances'] and results['metadatas'] and len(results['ids'][0]) > 0:
            for i, (report_id, distance, metadata) in enumerate(zip(
                results['ids'][0],
                results['distances'][0],
                results['metadatas'][0]
            )):
                result = {
                    'score': float(distance),  # Lower = more similar
                    'report_id': report_id,
                    **metadata
                }
                output.append(result)
        
        logger.info(f"✓ Found {len(output)} results")
        return output
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection_name,
            'persist_directory': self.persist_directory
        }
    
    def rebuild_index_from_mongodb(self, db):
        """
        Rebuild entire vector store from MongoDB scout_reports collection
        
        Useful for:
        - Initial setup
        - After adding many reports manually
        - Recovering from corrupted index
        
        Args:
            db: MongoDB database instance
        """
        logger.info("🔄 Rebuilding vector store from MongoDB...")
        
        # Fetch all scout reports
        reports = list(db["scout_reports"].find({}))
        logger.info(f"Found {len(reports)} reports in MongoDB")
        
        if not reports:
            logger.warning("No reports found in MongoDB")
            return
        
        # Reset collection
        self.reset()
        
        # Prepare documents for ChromaDB
        documents = []
        for report in reports:
            doc = {
                'text': report.get('text_for_vectorization', ''),
                'report_id': str(report['_id']),
                'player_id': str(report.get('player_id', '')),
                'player_name': report.get('player_name', 'Unknown'),
                'player_position': report.get('player_position', 'Unknown'),
                'player_nationality': report.get('player_nationality', 'Unknown'),
                'summary': report.get('summary', '')
            }
            documents.append(doc)
        
        # Add to vector store
        self.add_documents(documents)
        
        logger.info("✓ Vector store rebuild complete!")

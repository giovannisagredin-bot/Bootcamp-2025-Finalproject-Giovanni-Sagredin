"""
RAG Search Agent
Combines vector search + LLM to answer scout report queries
"""

import logging
from typing import List, Dict
from app.vectorstore.manager import VectorStoreManager
from src.llm.utils import GenerativeAIClient
from pymongo.database import Database
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class SearchAgent:
    """
    RAG Agent for semantic search of scout reports
    
    Flow:
    1. User query → Vector search (find similar reports)
    2. Fetch full details from MongoDB
    3. Build context for LLM
    4. LLM generates final answer
    """
    
    def __init__(self, vector_store: VectorStoreManager, llm_client: GenerativeAIClient, db: Database, top_k: int = 3):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.db = db
        self.top_k = top_k
        logger.info(f"SearchAgent initialized (top_k={top_k})")
    
    def search(self, query: str) -> Dict:
        """
        Perform RAG search
        
        Args:
            query: User query (e.g., "Find fast right-back good at crossing")
            
        Returns:
            Dict with 'answer' (LLM response), 'sources' (reports), 'query'
        """
        logger.info(f"RAG Search: '{query}'")
        
        # Step 1: Vector similarity search
        logger.info(f"Searching vector store (top_k={self.top_k})...")
        similar_reports = self.vector_store.similarity_search(query=query, top_k=self.top_k)
        
        if not similar_reports:
            logger.warning("No similar reports found")
            return {
                'answer': "No relevant scout reports found. Try a different search query.",
                'sources': [],
                'query': query
            }
        
        logger.info(f"Found {len(similar_reports)} similar reports")
        
        # Step 2: Fetch full details from MongoDB
        logger.info("Fetching full report details from MongoDB...")
        enriched_sources = self._enrich_sources(similar_reports)
        
        # Step 3: Generate answer with LLM
        logger.info("Generating answer with LLM...")
        answer = self._generate_answer(query, enriched_sources)
        
        logger.info("RAG search complete")
        
        return {
            'answer': answer,
            'sources': enriched_sources,
            'query': query
        }
    
    def _enrich_sources(self, similar_reports: List[Dict]) -> List[Dict]:
        """Fetch full report details from MongoDB"""
        enriched = []
        
        for report in similar_reports:
            report_id = report.get('report_id')
            
            try:
                full_report = self.db["scout_reports"].find_one({"_id": ObjectId(report_id)})
                
                if not full_report:
                    logger.warning(f"Report {report_id} not found in MongoDB")
                    continue
                
                enriched.append({
                    'score': report['score'],
                    'report_id': report_id,
                    'player_name': full_report.get('player_name', 'Unknown'),
                    'player_position': full_report.get('player_position', 'Unknown'),
                    'player_nationality': full_report.get('player_nationality', 'Unknown'),
                    'overall_rating': full_report.get('overall_rating'),
                    'potential': full_report.get('potential'),
                    'value_euro': full_report.get('value_euro'),
                    'summary': full_report.get('summary', ''),
                    'strengths': full_report.get('strengths', []),
                    'weaknesses': full_report.get('weaknesses', []),
                    'technical_skills': full_report.get('technical_skills', []),
                    'physical_attributes': full_report.get('physical_attributes', [])
                })
                
            except Exception as e:
                logger.error(f"Error enriching report {report_id}: {e}")
                continue
        
        return enriched
    
    def _generate_answer(self, query: str, sources: List[Dict]) -> str:
        """Generate answer using LLM with retrieved context"""
        
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"""
            Report #{i}:
            Player: {source['player_name']}
            Position: {source['player_position']}
            Nationality: {source['player_nationality']}
            Overall: {source['overall_rating']} | Potential: {source['potential']}
            Value: €{source.get('value_euro', 'N/A')}

            Summary: {source['summary']}
            Strengths: {', '.join(source['strengths'])}
            Weaknesses: {', '.join(source['weaknesses'])}
            Technical: {', '.join(source['technical_skills'])}
            Physical: {', '.join(source['physical_attributes'])}
            """.strip())
        
        context = "\n---\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are an expert football scout assistant. Answer the user's question based ONLY on the scout reports provided below.

User Question: {query}

Scout Reports:
{context}

Instructions:
- Provide a clear, concise answer based on the reports above
- Mention specific player names and key attributes
- Explain why each player matches (or doesn't match) the criteria
- If no perfect match, suggest the closest alternatives
- Keep it professional and structured

Answer:"""

        response = self.llm_client.generate(prompt)
        return response.strip()

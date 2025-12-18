"""
ETL Pipeline for Scout Reports
Extracts, Transforms, and Loads scout reports into structured format
"""

import logging
from datetime import datetime
from bson.objectid import ObjectId
from pymongo.database import Database
from src.llm.utils import GenerativeAIClient
from app.pipeline.toxicity import ToxicityAnalyzer
from app.pipeline.exceptions import ToxicReportError


logger = logging.getLogger(__name__)


class ScoutReportPipeline:
    """
    ETL Pipeline for processing scout reports
    
    Flow:
    1. EXTRACT: Read report text
    2. TRANSFORM: Validate toxicity → Fetch player → Standardize with LLM
    3. LOAD: Save to MongoDB → Prepare for vector DB
    """
    
    def __init__(
        self, 
        db: Database, 
        llm_client: GenerativeAIClient, 
        toxicity_analyzer: ToxicityAnalyzer,
        vector_store = None
    ):
        """
        Initialize ETL Pipeline
        
        Args:
            db: MongoDB database instance
            llm_client: LLM client for standardization (OpenAI/Gemini/Mock)
            toxicity_analyzer: Analyzer for checking toxic content
            vector_store: VectorStoreManager for ChromaDB (optional)
        """
        self.db = db
        self.llm_client = llm_client
        self.toxicity_analyzer = toxicity_analyzer
        self.vector_store = vector_store
        logger.info(f"ScoutReportPipeline initialized (vector_store={'enabled' if vector_store else 'disabled'})")
    
    def _extract(self, report_text: str) -> dict:
        """
        Phase 1: EXTRACT
        Validates and prepares raw report text
        """
        # Remove extra whitespace
        report_text = report_text.strip()
        
        # Validate minimum length
        if len(report_text) < 10:
            raise ValueError("Report text too short (minimum 10 characters required)")
        
        logger.info(f" Extracted report ({len(report_text)} characters)")
        
        return {
            "report_text": report_text
        }
    
    def _transform(self, extracted: dict, player_id: str) -> dict:
        """
        Phase 2: TRANSFORM
        Checks toxicity, fetches player data, standardizes with LLM
        
        """
        report_text = extracted["report_text"]
        
        # STEP 1: Check toxicity
        logger.info("⏳ Checking toxicity...")
        toxicity_result = self.toxicity_analyzer.analyze(report_text)
        
        if toxicity_result.is_toxic:
            logger.warning(f"✗ Report rejected (toxicity: {toxicity_result.toxicity_score:.2f})")
            raise ToxicReportError(
                toxicity_score=toxicity_result.toxicity_score,
                reason=toxicity_result.reason,
                categories=toxicity_result.categories
            )
        
        logger.info(f"✓ Report approved (toxicity: {toxicity_result.toxicity_score:.2f})")
        
        # STEP 2: Fetch player data from MongoDB
        logger.info(f"⏳ Fetching player data for ID: {player_id}")
       
        player = self.db["final-project"].find_one({"_id": ObjectId(player_id)})
        
        if not player:
            raise ValueError(f"Player not found with ID: {player_id}")
        
        logger.info(f"✓ Player found: {player.get('name', 'Unknown')}")


        
        # STEP 3: LLM standardization (extract structured data from report text)
        logger.info("⏳ Standardizing report with LLM...")
        structured_data = self._standardize_with_llm(report_text)
        logger.info("✓ Report standardized")
        
        # STEP 4: Combine player data + structured report
        logger.info("⏳ Combining data...")
        combined_document = self._combine_data(player, structured_data, report_text, toxicity_result.toxicity_score)
        logger.info("✓ Data combined")
        
        return combined_document
    






    def _standardize_with_llm(self, report_text: str) -> dict:
        
        #Extract structured information from scout report using LLM
        
       
        prompt = f"""Analyze this scout report and extract structured information.

    Scout Report:
    {report_text}

    Extract the following information in JSON format:
    {{
        "technical_skills": ["skill1", "skill2", ...],
        "physical_attributes": ["attribute1", "attribute2", ...],
        "strengths": ["strength1", "strength2", ...],
        "weaknesses": ["weakness1", "weakness2", ...],
        "summary": "Brief summary of the report (max 2 sentences)"
    }}

    Rules:
    - technical_skills: dribbling, passing, shooting, ball control, etc.
    - physical_attributes: speed, strength, stamina, height, etc.
    - strengths: positive aspects mentioned
    - weaknesses: negative aspects or areas to improve
    - summary: concise overview

    Return ONLY valid JSON, no markdown."""

        response = self.llm_client.generate(prompt)
        
        # Parse JSON response
        import json
        try:
            structured = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                structured = json.loads(json_match.group(1))
            else:
                # Fallback: empty structure
                raise ValueError("Failed to parse structured data from LLM response")
        
        return structured
    
    def _combine_data(self, player: dict, structured_data: dict, report_text: str, toxicity_score: float) -> dict:
        """
        Combine player data from MongoDB + structured report data into final document
        
        Args:
            player: Player document from MongoDB
            structured_data: Structured data extracted by LLM
            report_text: Original report text
            
        Returns:
            dict: Final document ready for MongoDB insertion
        """
        return {
            # Foreign key to player
            "player_id": player["_id"],
            
            # Denormalized player data (for performance)
            "player_name": player.get("name"),
            "player_position": player.get("positions"),
            "player_nationality": player.get("nationality"),
            "overall_rating": player.get("overall_rating"),
            "potential": player.get("potential"),
            "value_euro": player.get("value_euro"),
            "wage_euro": player.get("wage_euro"),

            
            # Original report
            "report_text_original": report_text,
            
            # Structured data from LLM
            "technical_skills": structured_data.get("technical_skills", []),
            "physical_attributes": structured_data.get("physical_attributes", []),
            "strengths": structured_data.get("strengths", []),
            "weaknesses": structured_data.get("weaknesses", []),
            "summary": structured_data.get("summary", ""),
            
            # Metadata
            "created_at": datetime.utcnow(),
            
            # Text for vectorization (will be used in LOAD phase)
            "text_for_vectorization": self._prepare_text_for_vectorization(player, structured_data)
        }
    
    def _prepare_text_for_vectorization(self, player: dict, structured_data: dict) -> str:
        """
        Prepare combined text for vector embedding
        """
        parts = [
            f"Player: {player.get('name', 'Unknown')}",
            f"Position: {player.get('positions', 'Unknown')}",
            f"Nationality: {player.get('nationality', 'Unknown')}",
            f"Overall Rating: {player.get('overall_rating', 'N/A')}",
            f"Potential: {player.get('potential', 'N/A')}",
            f"Value (Euro): {player.get('value_euro', 'N/A')}",
            f"Wage (Euro): {player.get('wage_euro', 'N/A')}",
            f"Summary: {structured_data.get('summary', '')}",
            f"Strengths: {', '.join(structured_data.get('strengths', []))}",
            f"Weaknesses: {', '.join(structured_data.get('weaknesses', []))}",
            f"Technical Skills: {', '.join(structured_data.get('technical_skills', []))}",
            f"Physical Attributes: {', '.join(structured_data.get('physical_attributes', []))}"
        ]
        
        return " | ".join(parts)
    
    
    
    def _load(self, transformed_document: dict) -> str:
        """
        Phase 3: LOAD
        Save document to MongoDB scout_reports collection + ChromaDB vector store
        
        Args:
            transformed_document: Final document from _transform phase
            
        Returns:
            str: Inserted document ID
        """
        logger.info("⏳ Saving to MongoDB...")
        
        # Insert into scout_reports collection
        result = self.db["scout_reports"].insert_one(transformed_document)
        report_id = str(result.inserted_id)
        
        logger.info(f"✓ Report saved with ID: {report_id}")
        
        # Add to vector store if available
        if self.vector_store:
            logger.info("⏳ Adding to vector store...")
            try:
                self.vector_store.add_documents([
                    {
                        'text': transformed_document.get('text_for_vectorization', ''),
                        'report_id': report_id,
                        'player_id': str(transformed_document.get('player_id', '')),
                        'player_name': transformed_document.get('player_name', 'Unknown'),
                        'player_position': transformed_document.get('player_position', 'Unknown'),
                        'player_nationality': transformed_document.get('player_nationality', 'Unknown'),
                        'summary': transformed_document.get('summary', '')
                    }
                ])
                logger.info("✓ Added to vector store")
            except Exception as e:
                logger.error(f"Failed to add to vector store: {e}")
                # Don't fail the entire pipeline if vector store fails
        
        return report_id
    
    def process_report(self, report_text: str, player_id: str) -> dict:
        """
        Main method: Process complete ETL pipeline for scout report
        
        Args:
            report_text: Raw scout report text
            player_id: Player ID from frontend autocomplete
            
        Returns:
            dict: Result with report_id and status
            
        Raises:
            ToxicReportError: If report contains toxic content
            ValueError: If validation fails
        """
        try:
            logger.info("=" * 20)
            logger.info("Starting ETL Pipeline")
            logger.info("=" * 20)
            
            # Phase 1: EXTRACT
            extracted = self._extract(report_text)
            
            # Phase 2: TRANSFORM
            transformed = self._transform(extracted, player_id)
            
            # Phase 3: LOAD
            report_id = self._load(transformed)
            
            logger.info("=" * 20)
            logger.info("ETL Pipeline completed successfully")
            logger.info("=" * 200)
            
            return {
                "status": "success",
                "report_id": report_id,
                "player_name": transformed["player_name"],
                "summary": transformed["summary"]
            }
            
        except ToxicReportError as e:
            logger.error(f"Report rejected due to toxicity: {e.reason}")
            raise
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
            raise
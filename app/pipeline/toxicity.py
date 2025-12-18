"""
Toxicity Analysis Module
Uses LLM with few-shot learning to detect toxic content in scout reports
"""

import json
import logging
from src.llm.utils import GenerativeAIClient
from app.models.schemas import ToxicityAnalysis


logger = logging.getLogger(__name__)


class ToxicityAnalyzer:
    """Analyzes scout reports for toxic content using LLM with few-shot examples."""
    
    def __init__(self, llm_client: GenerativeAIClient, threshold: float = 0.7):
        """
        Args:
            llm_client: LLM client (OpenAI, Gemini, or Mock)
            threshold: Score above which content is toxic (default: 0.7)
        """
        self.llm_client = llm_client
        self.threshold = threshold
        logger.info(f"ToxicityAnalyzer initialized with threshold={threshold}")
    
    def analyze(self, report_text: str) -> ToxicityAnalysis:
        """Analyze a scout report for toxic content"""
        logger.info(f"Analyzing report ({len(report_text)} chars)")
        
        # Step 1: Build prompt with few-shot examples
        prompt = self._build_prompt(report_text)
        
        # Step 2: Send to LLM for analysis
        response = self.llm_client.generate(prompt)
        
        # Step 3: Parse JSON response and extract score
        result = self._parse_response(response)
        
        # Step 4: Compare score against threshold to make decision
        return ToxicityAnalysis(
            is_toxic=result['toxicity_score'] >= self.threshold,
            toxicity_score=result['toxicity_score'],
            categories=result.get('categories', []),
            reason=result.get('reason', 'No explanation provided')
        )
    
    def _build_prompt(self, report_text: str) -> str:
        """Build few-shot prompt with examples to teach LLM what is toxic"""
        return f"""Analyze this football scout report for toxic content.
        If the report is not in english, translate it first.

=== CLEAN EXAMPLES (Low Toxicity - Professional Reports) ===
1. "Excellent technical player with great vision. Needs to improve defensive work rate." → Score: 0.05
2. "Solid defender with good positioning. Would benefit from improved pace." → Score: 0.03

=== BORDERLINE EXAMPLES (Moderate - Subjective but Not Toxic) ===
1. "Good player when motivated, but work rate is inconsistent." → Score: 0.20 (mild criticism)
2. "Talented but has reputation for being difficult with coaching staff." → Score: 0.25 (behavioral concern)

=== TOXIC EXAMPLES (High Toxicity - Unacceptable Content) ===
1. "Lazy player, typical of South American footballers. Always diving." → Score: 0.92 (ethnic stereotyping)
2. "This idiot can't pass the ball. Completely useless waste of space." → Score: 0.88 (insults, offensive language)
3. "For a woman, she's surprisingly good. Bit emotional, typical female trait." → Score: 0.95 (sexism, stereotypes)

Look for: racism, sexism, insults, stereotypes, discriminatory content, unprofessional language.

Report to analyze: "{report_text}"

Respond ONLY with JSON:
{{
  "toxicity_score": <0.0 to 1.0>,
  "categories": [<list like "racism", "insult", "stereotype" or empty>],
  "reason": "<brief explanation>"
}}"""
    
    def _parse_response(self, response: str):
        """Parse LLM response and extract toxicity information"""
        response = response.strip()
        
        # LLMs often wrap JSON in markdown code blocks (```json ... ```)
        # We need to remove these markers before parsing
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        
        try:
            # Parse the JSON string into a Python dictionary
            result = json.loads(response)
            
            # Clamp score to valid range [0.0, 1.0] in case LLM outputs invalid values
            # max(0, min(1, score)) ensures: if score > 1 → 1, if score < 0 → 0
            score = float(result.get("toxicity_score", 0.5))
            result["toxicity_score"] = max(0.0, min(1.0, score))
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse response: {e}")
            
            # Fallback: if JSON is malformed, try extracting score with regex
            # Looks for pattern like: toxicity_score: 0.85 or "toxicity_score": 0.85
            import re
            match = re.search(r"toxicity_score[\"']?\s*:\s*([0-9.]+)", response)
            if match:
                return {
                    "toxicity_score": float(match.group(1)),
                    "categories": [],
                   "reason": "Parsed from malformed response"
                }
            
        
            
            
            raise ValueError("Could not parse toxicity analysis response")
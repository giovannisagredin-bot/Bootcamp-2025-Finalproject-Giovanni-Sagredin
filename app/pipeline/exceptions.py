"""
Custom exceptions for ETL pipeline
"""


class ToxicReportError(Exception):
    """Raised when a report is rejected due to toxic content"""
    
    def __init__(self, toxicity_score: float, reason: str, categories: list, suggestion: str | None = None):
        self.toxicity_score = toxicity_score
        self.reason = reason
        self.categories = categories
        self.suggestion = suggestion or (
            "Please rewrite the report in a professional manner, "
            "avoiding offensive language and stereotypes."
        )
        
        message = f"Report rejected (toxicity: {toxicity_score:.2f}): {reason}"
        super().__init__(message)

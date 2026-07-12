"""Provides core functionalities for the guardrails module."""
import logging
from app.core.contracts import BaseResponse

logger = logging.getLogger(__name__)

class SanityFilter:
    """
    Fintech-grade fallback and sanity validation mechanism.
    Ensures that no unhandled exceptions leak to the Java backend and 
    that responses always conform to the strictly defined BaseResponse contract.
    """

    @staticmethod
    def get_safe_fallback_response(agent_id: str = "SystemGuardrail", error_msg: str = "Unknown Error") -> BaseResponse:
        """
        Generates a hardcoded, guaranteed-safe response when critical systems fail.
        Never leaks stack traces to the Java backend.
        """
        logger.error(f"System fallback triggered by {agent_id}. Reason: {error_msg}")
        return BaseResponse(
            agent=agent_id,
            intent="FALLBACK",
            status="FAILED",
            parameters={},
            message_to_user="Şu anda işleminizi gerçekleştiremiyorum. Lütfen daha sonra tekrar deneyiniz veya müşteri temsilcisine bağlanınız."
        )

    @staticmethod
    def validate_final_response(response: BaseResponse) -> BaseResponse:
        """
        Final pass to ensure the response doesn't contain nulls where strings are expected,
        or PII/System leaks in the user message.
        """
        if not response.message_to_user:
            response.message_to_user = "İşleminiz devam ediyor."
            
        # Fintech sanity check: Ensure we don't send raw SQL, Exceptions, or stack traces to the user
        suspicious_keywords = ["Exception", "Traceback", "SQL", "SELECT *", "ValueError", "KeyError", "TimeoutError"]
        if any(kw in response.message_to_user for kw in suspicious_keywords):
            logger.critical("Potential sensitive system data leak detected in message_to_user. Overwriting.")
            return SanityFilter.get_safe_fallback_response(response.agent, "Data Leak Prevention Triggered")

        return response

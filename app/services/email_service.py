import logging

logger = logging.getLogger(__name__)


def send_verification_email_placeholder(email: str, user_id: str) -> None:
    """Placeholder for future verification mail delivery.

    Intentionally non-functional for now; logs intent without sending.
    """
    domain = email.split("@")[-1] if "@" in email else "unknown"
    logger.info("verification_email_placeholder user_id=%s email_domain=%s", user_id, domain)

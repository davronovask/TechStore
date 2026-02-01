import threading
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email_async(subject: str, message: str, recipient: str) -> None:
    def task():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,  # пока дебажим
            )
        except Exception as e:
            logger.exception("EMAIL ERROR: %s", e)

    threading.Thread(target=task, daemon=True).start()
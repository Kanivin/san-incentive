from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class IncentivesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incentives'

    def ready(self):
        import incentives.signals.change_log_signal
        from .scheduler import start
        logger.info("Starting APScheduler inside Django app")
        start()
        logger.info("Completed APScheduler inside Django app")
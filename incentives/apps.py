from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incentives'

    def ready(self):
        import incentives.signals.change_log_signal
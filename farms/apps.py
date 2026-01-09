from django.apps import AppConfig


class FarmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'farms'
    
    def ready(self):
        """Register signals when the app is ready"""
        import farms.signals
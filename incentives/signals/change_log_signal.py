import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from incentives.models import ChangeLog  # Correct import
from django.utils.timezone import now
import sys
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder


EXCLUDED_MODELS = ['ChangeLog', 'Role', 'Module', 'Permission', 'UserProfile', 'Segment', 'LeadSource']  # prevent recursion

def clean_dict(data):
    """Utility to clean dictionary and convert non-serializable data."""
    clean = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            clean[key] = value.isoformat()  # Convert datetime to ISO 8601 string
        elif isinstance(value, (str, int, bool, float)):  # Primitive types
            clean[key] = value
        else:
            clean[key] = str(value)  # Convert other non-serializable types to string
    return clean

def log_change(instance, action):
    """Log the changes made to the model instance."""
    data = model_to_dict(instance)  # Get the model's field data
    cleaned_data = clean_dict(data)  # Clean and serialize the data properly

    if instance.__class__.__name__ == "TargetTransaction":
        return
    if instance.__class__.__name__ == "Transaction":
        return    
 
    # Create the change log entry
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        content_object=instance,
        change_type=action,
        changed_data=cleaned_data,  # Cleaned data
        new_data=cleaned_data       # New data after modification
    )

@receiver(post_save)
def auto_log_save(sender, instance, created, **kwargs):
    """Log changes on save (create or update)."""
    # Skip during migrate or makemigrations
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return

    if sender.__name__ in EXCLUDED_MODELS:
        return

    # Log the change based on create or update
    log_change(instance, 'create' if created else 'update')

@receiver(post_delete)
def auto_log_delete(sender, instance, **kwargs):
    """Log changes on delete."""
    if sender.__name__ in EXCLUDED_MODELS:
        return

    # Log the delete action
    log_change(instance, 'delete')

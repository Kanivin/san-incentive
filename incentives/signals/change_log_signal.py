import json  # Ensure this import is at the top of the file
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from incentives.models import ChangeLog  # Correct import
from django.utils.timezone import now
import sys
from datetime import datetime
from django.utils.timezone import is_naive, make_naive
from django.core.serializers.json import DjangoJSONEncoder


EXCLUDED_MODELS = ['ChangeLog','Role','Module','Permission','UserProfile','Segment','LeadSource']  # prevent recursion

def clean_dict(data):
    for key, value in data.items():
        if isinstance(value, datetime):  # datetime class should be used here, not the module
            if is_naive(value):
                data[key] = value.isoformat()
            else:
                data[key] = make_naive(value).isoformat()
    return data

def log_change(instance, action):
    # Prepare change data and serialize datetime properly
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        try:
            # Try serializing the value
            json.dumps(value, cls=DjangoJSONEncoder)  # Test if the value is serializable
            data[field.name] = value
        except TypeError:
            if isinstance(value, datetime):  # Check directly for datetime instances
                data[field.name] = value.isoformat()  # Serialize datetime to ISO format
            else:
                data[field.name] = str(value)  # Convert other types to string

    # Log the change
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        new_data=clean_dict(model_to_dict(instance)),
        change_type=action,
        changed_data=data
    )

@receiver(post_save)
def auto_log_save(sender, instance, created, **kwargs):
    # Skip during migrate or makemigrations
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return
    if sender.__name__ in EXCLUDED_MODELS:
        return
    log_change(instance, 'create' if created else 'update')


@receiver(post_delete)
def auto_log_delete(sender, instance, **kwargs):
    if sender.__name__ in EXCLUDED_MODELS:
        return
    log_change(instance, 'delete')

from celery import shared_task
from .models import JobRunLog
import time
from datetime import datetime

@shared_task(bind=True)
def monthly_sales_incentive(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Monthly Sales Incentive Calculation", status="Running")
    try:
        time.sleep(5)  # simulate processing
        output = "[INFO] Calculated monthly incentive"
        log.status = "Success"
        log.output = output
    except Exception as e:
        log.status = "Failed"
        log.output = str(e)
    finally:
        log.duration = datetime.now() - start
        log.save()

@shared_task(bind=True)
def annual_target_achievement(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Annual Target Achievement", status="Running")
    try:
        time.sleep(5)
        output = "[INFO] Annual target processing complete"
        log.status = "Success"
        log.output = output
    except Exception as e:
        log.status = "Failed"
        log.output = str(e)
    finally:
        log.duration = datetime.now() - start
        log.save()

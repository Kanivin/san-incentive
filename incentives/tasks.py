from celery import shared_task
from .models import JobRunLog, ScheduledJob  # Ensure ScheduledJob is also imported
import time
from datetime import datetime, timedelta


@shared_task(bind=True)
def monthly_sales_incentive(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Monthly Sales Incentive Calculation", status="Running")
    try:
        time.sleep(5)  # Simulate processing
        output = "[INFO] Calculated monthly incentive"
        log.status = "success"
        log.output = output
        try:
            job = ScheduledJob.objects.get(name="Monthly Sales Incentive Calculation")
            job.last_run = start
            # Calculate next run: 1st of next month at 12:00 AM
            next_month = (start.replace(day=1) + timedelta(days=32)).replace(day=1)
            job.next_run = next_month.replace(hour=0, minute=0, second=0, microsecond=0)
            job.save()
        except Exception as e:
            log.status = "failed"
            log.output += f"\n[ERROR] ScheduledJob update failed: {e}"
    except Exception as e:
        log.status = "failed"
        log.output = str(e)
    finally:
        log.duration = datetime.now() - start
        log.save()


@shared_task(bind=True)
def annual_target_achievement(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Annual Target Achievement", status="Running")
    try:
        time.sleep(5)  # Simulate processing
        output = "[INFO] Annual target processing complete"
        log.status = "success"
        log.output = output
        try:
            job = ScheduledJob.objects.get(name="Annual Target Achievement")
            job.last_run = start
            # Set next_run to January 1st of next year at 2:00 AM
            next_year = start.replace(year=start.year + 1, month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
            job.next_run = next_year
            job.save()
        except Exception as e:
            log.status = "failed"
            log.output += f"\n[ERROR] ScheduledJob update failed: {e}"
    except Exception as e:
        log.status = "failed"
        log.output = str(e)
    finally:
        log.duration = datetime.now() - start
        log.save()

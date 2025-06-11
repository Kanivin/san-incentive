from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from .tasks import monthly_sales_incentive, annual_target_achievement
import logging
from datetime import datetime
from django.utils import timezone
import calendar

logger = logging.getLogger(__name__)

# Initialize scheduler with timezone
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

# Monthly job: runs daily at 23:00 but only executes on the last day of the month
@scheduler.scheduled_job(CronTrigger(hour=23, minute=0))
def run_monthly_incentive():
    
    today = datetime.now().date()
    last_day = calendar.monthrange(today.year, today.month)[1]
    current_month= timezone.now().month

    if today.day == last_day:
        logger.info("Running monthly sales incentive task (Last day of the month)")
        monthly_sales_incentive(current_month)
    else:
        logger.info("Skipping monthly sales incentive task — today is not the last day of the month")

# Annual job: runs on December 31st at 23:30
@scheduler.scheduled_job(CronTrigger(month=12, day=31, hour=23, minute=30))
def run_annual_target_achievement_task():
    logger.info("Running annual target achievement task (Dec 31, 23:30)")
    annual_target_achievement()

# Job every 30 minutes
# @scheduler.scheduled_job(CronTrigger(minute='*/30'))
# def run_incentive_every_30_minutes():
#    logger.info("Running 30-minute periodic incentive task")
#    monthly_sales_incentive()

# Scheduler start function
def start():
    try:
        scheduler.start()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

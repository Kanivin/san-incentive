from celery import shared_task
from django.utils import timezone
from .models import JobRunLog, ScheduledJob, PayoutTransaction, IncentiveSetup
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@shared_task(bind=True)
def monthly_sales_incentive(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Monthly Sales Incentive Calculation", status="Running")
    
    try:
        # time.sleep(5)  # Simulate processing

        current_year = timezone.now().year
        pending_payouts = PayoutTransaction.objects.filter(payout_status='Pending', is_latest=True)

        for payout in pending_payouts:
            deal = payout.deal
            setup = IncentiveSetup.objects.filter(financial_year=str(current_year)).order_by('-created_at').first()

            if not deal or not deal.dealWonDate or not setup:
                continue

            component_type = payout.incentive_transaction.incentive_component_type

            if component_type == "new_market":
                cutoff_date = timezone.now().date() - relativedelta(months=setup.new_market_eligibility_months or 0)

                if deal.dealWonDate < cutoff_date:
                    payout.payout_status = 'ReadyToPay'
                    payout.payout_message = f"Eligible based on deal won date: {deal.dealWonDate}"
                    payout.save()
                else:
                    payout.payout_message = f"Not eligible - deal date {deal.dealWonDate} before cutoff {cutoff_date}"
                    payout.save()
            else:
                payout.payout_status = 'ReadyToPay'
                payout.payout_message = f"Ready To Pay for: {component_type}"
                payout.save()

        output = "[INFO] Calculated monthly incentive"
        log.status = "success"
        log.output = output

        try:
            job = ScheduledJob.objects.get(name="Monthly Sales Incentive Calculation")
            job.last_run = start
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

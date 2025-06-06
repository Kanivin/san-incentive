from celery import shared_task
from django.utils import timezone
from .models import JobRunLog, ScheduledJob, PayoutTransaction, TargetTransaction, IncentiveSetup , Deal
import time
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@shared_task(bind=True)
def monthly_sales_incentive(self):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Monthly Sales Incentive Calculation", status="Running")
    all_success = True  # ← Track global success
    output_lines = []   # ← Collect log output

    try:
        # time.sleep(5)  # Simulate processing

        current_year = timezone.now().year
        setup = IncentiveSetup.objects.filter(financial_year=str(current_year)).order_by('-created_at').first()

        pending_payouts = PayoutTransaction.objects.filter(payout_status='Pending', is_latest=True)
       
        for payout in pending_payouts:
            deal = payout.deal
           
            if not deal or not deal.dealWonDate or not setup:
                continue

            component_type = payout.incentive_transaction.incentive_component_type

            try:
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
            except Exception as e:
                all_success = False
                output_lines.append(f"[ERROR] Payout calc for deal {deal.id}: {e}")    

        # process_subscription_incentive
        approved_deals = Deal.objects.filter(status='Approved')

        for deal in approved_deals:           
            
            if not deal or not deal.subDate or not setup:
                continue

            try:
                cutoff_date = timezone.now().date() - relativedelta(months=setup.min_subscription_month or 0)

                if deal.subDate < cutoff_date:

                    sub_amount = deal.subAmount
                    success = True
                    payout_split = {
                        'dealownerSalesPerson': (deal.dealownerSalesPerson, 'Deal Owner', setup.deal_owner),
                        'leadSource': (deal.leadSource, 'Lead Source', setup.lead_source),
                        'followUpSalesPerson': (deal.followUpSalesPerson, 'Follow Up', setup.follow_up),
                        'demo1SalesPerson': (deal.demo1SalesPerson, 'Demo 1', setup.demo_1),
                        'demo2SalesPerson': (deal.demo2SalesPerson, 'Demo 2', setup.demo_2),
                    }

                    for field_name, (user, label, percent) in payout_split.items():
                        if user and percent:
                            try:
                                incentive_amount = (sub_amount * percent) / Decimal('100.0')
                                TargetTransaction.objects.create(
                                    deal=deal,
                                    user=user,
                                    transaction_type='Earned',
                                    incentive_component_type='subscription',
                                    amount=incentive_amount,
                                    eligibility_status='Eligible',
                                    eligibility_message=f'Subscription incentive {percent:.2f}%',
                                    notes=f'{label} gets {percent:.2f}% of ₹{sub_amount}',
                                    created_by="system-mjob"
                                )
                            except Exception as e:
                                success = False
                                all_success = False
                                print(f" Error Subscription incentive for {label} → {e}")
                        else:
                            print(f"Skipped {label} → Missing user or percent")
                if success:
                    deal.status = 'Completed'
                    deal.save()
            except Exception as e:
                all_success = False
                output_lines.append(f"[ERROR] Subscription handling failed for deal {deal.id}: {e}")                

        if all_success:
            output_lines.append("[INFO] Calculated monthly incentive")
            log.status = "success"
        else:
            log.status = "failed"
            output_lines.append("[ERROR] Some payouts or deals failed. Check logs.")

        log.output = "\n".join(output_lines)

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

from django.utils import timezone
from django.db import transaction
from .models import (
    JobRunLog, ScheduledJob, PayoutTransaction, 
    AnnualTarget, TargetTransaction, IncentiveSetup, 
    Deal, UserProfile
)
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q
from incentives.utils.monthly_incentive_engine import MonthlyRuleEngine

def monthly_sales_incentive(run_month):
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Monthly Sales Incentive Calculation", status="Running")
    all_success = True
    output_lines = []

    try:
        MonthlyRuleEngine(run_month).run_rules()

        current_year = timezone.now().year
        setup = IncentiveSetup.objects.filter(financial_year=str(current_year)).order_by('-created_at').first()

        pending_payouts = PayoutTransaction.objects.filter(payout_status='Pending', is_latest=True)

        for payout in pending_payouts:
            deal = getattr(payout, 'deal', None)
            component_type = getattr(payout.incentive_transaction, 'incentive_component_type', None)

            if not deal or not deal.dealWonDate or not setup:
                continue

            try:
                if component_type == "new_market":
                    cutoff_date = timezone.now().date() - relativedelta(months=setup.new_market_eligibility_months or 0)
                    if deal.dealWonDate < cutoff_date:
                        payout.payout_status = 'ReadyToPay'
                        payout.payout_message = f"Eligible based on deal won date: {deal.dealWonDate}"
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

        approved_deals = Deal.objects.filter(status='Approved')

        for deal in approved_deals:
            if not deal or not deal.subDate or not setup:
                continue

            try:
                sub_amount = deal.subAmount or Decimal('0.0')
                                 
                success = True
                if deal.dealType == 'domestic':
                    payout_split = {
                        'Deal Owner': (deal.dealownerSalesPerson, setup.domestic_deal_owner),
                        'Lead Source': (deal.leadSource, setup.domestic_lead_source),
                        'Follow Up': (deal.followUpSalesPerson, setup.domestic_follow_up),
                        'Demo 1': (deal.demo1SalesPerson, setup.domestic_demo_1),
                        'Demo 2': (deal.demo2SalesPerson, setup.domestic_demo_2),
                    }
                else:
                    payout_split = {
                        'Deal Owner': (deal.dealownerSalesPerson, setup.international_deal_owner),
                        'Lead Source': (deal.leadSource, setup.international_lead_source),
                        'Follow Up': (deal.followUpSalesPerson, setup.international_follow_up),
                        'Demo 1': (deal.demo1SalesPerson, setup.international_demo_1),
                        'Demo 2': (deal.demo2SalesPerson, setup.international_demo_2),
                    }                
                for label, (user, percent) in payout_split.items():
                    if user and percent:
                        try:
                            incentive_amount = (sub_amount * percent) / Decimal('100.0')
                            TargetTransaction.objects.create(
                                    deal=deal,
                                    user=user,
                                    transaction_type='Earned',
                                    incentive_component_type='subscription',
                                    amount=incentive_amount,
                                    eligibility_status='Ineligible',
                                    eligibility_message=f'Subscription incentive {percent:.2f}%',
                                    notes=f'{label} gets {percent:.2f}% of ₹{sub_amount}',
                                    created_by="system-mjob"
                                    )                            
                        except Exception as e:
                            success = False
                            all_success = False
                            output_lines.append(f"[ERROR] Subscription incentive for {label} → {e}")
                    else:
                        output_lines.append(f"[INFO] Skipped {label} → Missing user or percent")

                if success:
                    deal.status = 'Completed'
                    deal.yearly_rule_executed = True            
                    deal.save()

            except Exception as e:
                all_success = False
                output_lines.append(f"[ERROR] Subscription handling failed for deal {deal.id}: {e}")

             # After creation, if deal is eligible, update transactions to 'Eligible'
            cutoff_date = timezone.now().date() - relativedelta(months=setup.min_subscription_month or 0) 
            if deal.subDate < cutoff_date:
                TargetTransaction.objects.filter(deal=deal).update(
                eligibility_status='Eligible',
                eligibility_message='Subscription is eligibility')
         
        log.status = "success" if all_success else "failed"
        output_lines.append("[INFO] Monthly incentives processed" if all_success else "[ERROR] Issues occurred during monthly incentive calculation")

        log.output = "\n".join(output_lines)

        try:
            job = ScheduledJob.objects.get(name="Monthly Sales Incentive Calculation")
            job.last_run = start
            next_month = (start.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            job.next_run = next_month
            job.save()
        except Exception as e:
            log.status = "failed"
            log.output += f"\n[ERROR] ScheduledJob update failed: {e}"

    except Exception as e:
        log.status = "failed"
        log.output = f"[CRITICAL ERROR] Task failed: {e}"

    finally:
        log.duration = datetime.now() - start
        log.save()


def annual_target_achievement():
    start = datetime.now()
    log = JobRunLog.objects.create(job_name="Annual Target Achievement", status="Running")
    all_success = True
    output_lines = []

    try:
        current_year = timezone.now().year
        setup = IncentiveSetup.objects.filter(financial_year=str(current_year)).order_by('-created_at').first()
        users = UserProfile.objects.filter(Q(user_type__name='saleshead') | Q(user_type__name='salesperson'))

        for user in users:
            if not user or not setup:
                continue

            try:
                annual_target = AnnualTarget.objects.get(employee_id=user.id, financial_year=current_year, status='Not Completed')
            except AnnualTarget.DoesNotExist:
                continue

            try:
                with transaction.atomic():
                    total_target = TargetTransaction.objects.filter(
                        user_id=user.id,
                        transaction_type='Earned',
                        transaction_date__year=current_year
                    ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

                    annual_target_amount = annual_target.annual_target_amount or Decimal('0.0')
                    net_salary = annual_target.net_salary or Decimal('0.0')
                    target_percentage = (total_target / annual_target_amount) * 100 if annual_target_amount > 0 else Decimal('0.0')

                    annual_target_incentive = Decimal('0.0')
                    if target_percentage >= 100:
                        annual_target_incentive = net_salary * Decimal('2.0')
                    elif target_percentage >= 95:
                        annual_target_incentive = net_salary * Decimal('1.5')
                    elif target_percentage >= 90:
                        annual_target_incentive = net_salary * Decimal('1.25')
                    elif target_percentage >= 75:
                        annual_target_incentive = net_salary * Decimal('1.0')

                    PayoutTransaction.objects.create(
                        user=user,
                        incentive_person_type=f'{current_year} Annual Target Incentive',
                        payout_amount=annual_target_incentive,
                        payout_status='ReadyToPay',
                        payment_method='Bank Transfer',
                        created_by='system-yjob',
                    )

                    # Subscription incentive
                    if target_percentage >= 100:
                        sub_percent = setup.subscription_100_per_target or Decimal('0.00')
                    elif target_percentage >= 75:
                        sub_percent = setup.subscription_75_per_target or Decimal('0.00')
                    elif target_percentage >= 50:
                        sub_percent = setup.subscription_50_per_target or Decimal('0.00')
                    else:
                        sub_percent = setup.subscription_below_50_per or Decimal('0.00')

                    subscription_incentive = total_target * (sub_percent / 100)

                    PayoutTransaction.objects.create(
                        user=user,
                        incentive_person_type=f'{current_year} Annual Subscription Incentive',
                        payout_amount=subscription_incentive,
                        payout_status='ReadyToPay',
                        payment_method='Bank Transfer',
                        created_by='system-yjob',
                    )

                    annual_target.status = 'Completed'
                    annual_target.save(update_fields=['status'])

            except Exception as e:
                all_success = False
                output_lines.append(f"[ERROR] Failed for user {user.id} ({user.fullname}): {e}")

        log.status = "success" if all_success else "failed"
        output_lines.append("[INFO] Annual target incentives processed." if all_success else "[ERROR] Some annual incentives failed.")

        log.output = "\n".join(output_lines)

        try:
            job = ScheduledJob.objects.get(name="Annual Target Achievement")
            job.last_run = start
            next_year = start.replace(year=start.year + 1, month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
            job.next_run = next_year
            job.save()
        except Exception as e:
            log.status = "failed"
            log.output += f"\n[ERROR] Failed to update ScheduledJob: {e}"

    except Exception as e:
        log.status = "failed"
        log.output = f"[CRITICAL ERROR] Task failed: {e}"

    finally:
        log.duration = datetime.now() - start
        log.save()

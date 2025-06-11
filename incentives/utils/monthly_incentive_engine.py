from collections import defaultdict
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ..models import (
    Transaction, PayoutTransaction, IncentiveSetup,
    SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget, TargetTransaction,
    HighValueDealSlab, UserProfile
)


class MonthlyRuleEngine:

    def __init__(self, run_month):
        self.run_month = run_month
        self.setup = None
        self.deals_in_month = None
        self.initialize_setup()

    def get_current_financial_year(self):
        return timezone.now().year

    def initialize_setup(self):
        financial_year = self.get_current_financial_year()
              
        self.setup = IncentiveSetup.objects.filter(financial_year=financial_year).last()
        if not self.setup:
            print(f"[Warning] No IncentiveSetup found for the year {financial_year}.")

        self.deals_in_month = Deal.objects.filter(
            status='Approved',
            monthly_rule_executed=False,
            dealWonDate__year=financial_year,
            dealWonDate__month=self.run_month
        )
        if not self.deals_in_month.exists():
            print(f"[Warning] No Approved deal found for the year {financial_year} month {self.run_month}.")

    def run_rules(self):
        if not self.setup:
            print("[Warning] IncentiveSetup is not initialized.")
            return

        self.process_all_incentive()

    def process_all_incentive(self):
        user_setup_totals = defaultdict(Decimal)
        user_monthly_subscription_totals = defaultdict(Decimal)
        user_deal_tracker = set()

        for deal in self.deals_in_month:
            participants = [
                deal.dealownerSalesPerson,
                deal.leadSource,
                deal.followUpSalesPerson,
                deal.demo1SalesPerson,
                deal.demo2SalesPerson,
            ]
            for user in filter(None, participants):
                key = (user.id, deal.id)
                if key not in user_deal_tracker:
                    user_setup_totals[user.id] += Decimal(deal.setupCharges or 0)
                    user_monthly_subscription_totals[user.id] += Decimal(deal.monthlySubscription or 0)
                    user_deal_tracker.add(key)

        for deal in self.deals_in_month:
            try:
                
                deal_type = deal.dealType.lower()
                deal_segment = deal.segment
                
                try:
                    setup_charges = Decimal(deal.setupCharges or 0)
                    monthly_subscription_charges = Decimal(deal.monthlySubscription or 0)
                except InvalidOperation:
                    print(f"[ERROR] Invalid numeric values in deal {deal.id}. Skipping...")
                    continue

                payout_split = self.get_payout_split(deal)
                if setup_charges != 0:
                    self.process_setup_incentive(deal, payout_split, deal_type, setup_charges, user_setup_totals)
                if monthly_subscription_charges != 0:    
                    self.process_topper_incentive(deal, payout_split, deal_type, deal_segment, monthly_subscription_charges, user_monthly_subscription_totals)
                    self.process_high_value_incentive(deal, payout_split, monthly_subscription_charges)
                if deal.newMarketPenetration == 'Yes':
                    self.process_new_market_incentive(deal, payout_split)
                # Mark as executed after successful processing
                deal.monthly_rule_executed = True
                deal.save(update_fields=['monthly_rule_executed'])
            except Exception as e:
                # Optional: log or handle the error without stopping the loop
                print(f"[ERROR] Skipping deal {deal.id} due to: {e}")

    def get_payout_split(self, deal):
        if deal.dealType == 'domestic':
            return {
                'Deal Owner': (deal.dealownerSalesPerson, self.setup.domestic_deal_owner),
                'Lead Source': (deal.leadSource, self.setup.domestic_lead_source),
                'Follow Up': (deal.followUpSalesPerson, self.setup.domestic_follow_up),
                'Demo 1': (deal.demo1SalesPerson, self.setup.domestic_demo_1),
                'Demo 2': (deal.demo2SalesPerson, self.setup.domestic_demo_2),
            }
        return {
            'Deal Owner': (deal.dealownerSalesPerson, self.setup.international_deal_owner),
            'Lead Source': (deal.leadSource, self.setup.international_lead_source),
            'Follow Up': (deal.followUpSalesPerson, self.setup.international_follow_up),
            'Demo 1': (deal.demo1SalesPerson, self.setup.international_demo_1),
            'Demo 2': (deal.demo2SalesPerson, self.setup.international_demo_2),
        }

    def process_setup_incentive(self, deal, payout_split, deal_type, setup_charges, user_setup_totals):
        for label, (user, percent) in payout_split.items():
            label_with_tag = f"{label}(Setup)"
            if user and percent:
                try:
                    total_user_amount = user_setup_totals.get(user.id, Decimal('0.00'))
                    slab = SetupChargeSlab.objects.filter(
                        incentive_setup=self.setup,
                        deal_type_setup=deal_type,
                        min_amount__lte=total_user_amount,
                        max_amount__gte=total_user_amount
                    ).first()

                    if not slab:
                        print(f"[INFO] {user.fullname} → No matching slab for ₹{total_user_amount}")
                        continue

                    incentive_amount = (setup_charges * slab.incentive_percentage) / Decimal('100.0')
                    incentive_amount_user = (incentive_amount * percent) / Decimal('100.0')

                    transaction = Transaction.objects.create(
                        deal_id=deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='setup',
                        amount=incentive_amount_user,
                        eligibility_status='Eligible',
                        eligibility_message='Matched Setup Charge Slab',
                        notes=f'Slab {slab.min_amount}-{slab.max_amount} @ {slab.incentive_percentage}%',
                        created_by="system-mjob"
                    )
                    self.create_payouts(deal, transaction, user, label_with_tag, incentive_amount_user)
                except Exception as e:
                    print(f"[ERROR] Processing {label} for deal {deal.id} → {e}")
            else:
                print(f"[INFO] Skipped {label} → Missing user or percent")

    def process_topper_incentive(self, deal, payout_split, deal_type, segment, monthly_subscription_charges, user_monthly_subscription_totals):
        for label, (user, percent) in payout_split.items():
            label_with_tag = f"{label}(Topper Month)"
            if user and percent:
                try:
                    total_user_amount = user_monthly_subscription_totals.get(user.id, Decimal('0.00'))
                    slab = TopperMonthSlab.objects.filter(
                        incentive_setup=self.setup,
                        deal_type_top__in=[deal_type, 'all'],
                        segment=segment,
                        min_subscription__lte=total_user_amount
                    ).order_by('-min_subscription').first()

                    if not slab:
                        print(f"[INFO] {user.fullname} → No matching slab for ₹{total_user_amount}")
                        continue

                    incentive_amount = (monthly_subscription_charges * slab.incentive_percentage) / Decimal('100.0')
                    incentive_amount_user = (incentive_amount * percent) / Decimal('100.0')

                    transaction = Transaction.objects.create(
                        deal_id=deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='topper_month',
                        amount=incentive_amount_user,
                        eligibility_status='Eligible',
                        eligibility_message='Top performer of the month',
                        notes=f'Segment: {segment.name}, Slab: ≥ {slab.min_subscription}',
                        created_by="system-mjob"
                    )
                    self.create_payouts(deal, transaction, user, label_with_tag, incentive_amount_user)
                except Exception as e:
                    print(f"[ERROR] Processing {label} for deal {deal.id} → {e}")
            else:
                print(f"[INFO] Skipped {label} → Missing user or percent")

    def process_high_value_incentive(self, deal, payout_split, monthly_subscription_charges):
        slab = HighValueDealSlab.objects.filter(
            incentive_setup=self.setup,
            min_amount__lte=monthly_subscription_charges,
            max_amount__gte=monthly_subscription_charges
        ).first()

        if not slab:
            return

        for label, (user, percent) in payout_split.items():
            label_with_tag = f"{label}(High Value Deal)"
            if user and percent:
                try:
                    incentive_amount = (monthly_subscription_charges * slab.incentive_percentage) / Decimal('100.0')
                    incentive_amount_user = (incentive_amount * percent) / Decimal('100.0')

                    transaction = Transaction.objects.create(
                        deal_id=deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='high_value_deal',
                        amount=incentive_amount_user,
                        eligibility_status='Eligible',
                        eligibility_message='High value deal incentive matched',
                        notes=f'Slab: {slab.min_amount}-{slab.max_amount}',
                        created_by="system-mjob"
                    )
                    self.create_payouts(deal, transaction, user, label_with_tag, incentive_amount_user)
                except Exception as e:
                    print(f"[ERROR] Processing {label} for deal {deal.id} → {e}")
            else:
                print(f"[INFO] Skipped {label} → Missing user or percent")

    def process_new_market_incentive(self, deal, payout_split):
        if deal.newMarketPenetration != 'Yes':
            return

        incentive_amount = self.setup.new_market_deal_incentive

        for label, (user, percent) in payout_split.items():
            label_with_tag = f"{label}(New Market)"
            if user and percent:
                try:
                    incentive_amount_user = (incentive_amount * percent) / Decimal('100.0')
                    transaction = Transaction.objects.create(
                        deal_id=deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='new_market',
                        amount=incentive_amount_user,
                        eligibility_status='Eligible',
                        eligibility_message='Client in new market window',
                        notes='New Client onboarded',
                        created_by="system-mjob"
                    )
                    self.create_payouts(deal, transaction, user, label_with_tag, incentive_amount_user)
                except Exception as e:
                    print(f"[ERROR] Processing {label} for deal {deal.id} → {e}")
            else:
                print(f"[INFO] Skipped {label} → Missing user or percent")

    def create_payouts(self, deal, transaction, user, label, incentive_amount):
        try:
            PayoutTransaction.objects.create(
                deal=deal,
                incentive_transaction=transaction,
                user=user,
                incentive_person_type=label.lower().replace(' ', '_'),
                payout_amount=incentive_amount,
                payout_status='Pending',
                payment_method='Bank Transfer',
                created_by="system-mjob",
            )
        except Exception as e:
            print(f"[ERROR] {label} → Failed to create payout: {e}")
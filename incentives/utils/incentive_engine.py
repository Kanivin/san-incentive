from ..models import (
    Transaction, PayoutTransaction, IncentiveSetup,
    SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget,
    HighValueDealSlab, UserProfile
)
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from decimal import Decimal
from datetime import date


class DealRuleEngine:

    def __init__(self, deal):
        self.deal = deal
        self.setup = None
        self.initialize_setup()

    def get_current_financial_year(self):
        current_date = date.today()
        start_year = current_date.year - 1 if current_date.month < 4 else current_date.year
        return f"{start_year}-{start_year + 1}"

    def initialize_setup(self):
        financial_year = self.get_current_financial_year()
        self.setup = IncentiveSetup.objects.filter(financial_year=financial_year).last()
        if not self.setup:
            print(f"[⚠️ Warning] No IncentiveSetup found for the year {financial_year}.")

    def run_rules(self):
        if not self.setup:
            return
        self.process_setup_incentive()
        self.process_new_market_incentive()
        self.process_topper_month_incentive()
        self.process_high_value_deal_incentive()
        self.process_subscription_incentive()

    def process_setup_incentive(self):
        deal_amount = self.deal.setupCharges
        deal_type = self.deal.dealType.lower()

        slab = SetupChargeSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_setup=deal_type,
            min_amount__lte=deal_amount,
            max_amount__gte=deal_amount
        ).first()

        if not slab:
            return

        incentive_amount = (deal_amount * slab.incentive_percentage) / Decimal('100.0')

        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='setup',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Matched Setup Charge Slab',
            notes=f'Slab {slab.min_amount}-{slab.max_amount} @ {slab.incentive_percentage}%',
            created_by=self.deal.created_by,
        )

        self.create_payouts(transaction, incentive_amount)

    def process_new_market_incentive(self):
        if not self.setup.new_market_eligibility_months or not self.setup.new_market_deal_incentive:
            return

        client_created_at = getattr(self.deal.clientName, 'created_at', None)
        if not client_created_at:
            return

        cutoff_date = timezone.now() - relativedelta(months=self.setup.new_market_eligibility_months)
        if client_created_at > cutoff_date:
            incentive_amount = self.setup.new_market_deal_incentive

            transaction = Transaction.objects.create(
                deal_id=str(self.deal.id),
                transaction_type='Earned',
                incentive_component_type='new_market',
                amount=incentive_amount,
                eligibility_status='Eligible',
                eligibility_message='Client in new market window',
                notes=f'Client onboarded on {client_created_at.date()}',
                created_by=self.deal.created_by,
            )

            self.create_payouts(transaction, incentive_amount)

    def process_topper_month_incentive(self):
        deal_segment = self.deal.segment
        deal_amount = self.deal.monthlySubscription
        deal_type = self.deal.dealType.lower()


        slabs = TopperMonthSlab.objects.filter(
        incentive_setup=self.setup,
        deal_type_top__in=[deal_type, 'all'],
        segment=deal_segment,
        )


        if not slabs.exists():
            return

        eligible_slabs = slabs.filter(
            min_subscription__lte=self.deal.monthlySubscription
        ).order_by('-min_subscription')

        slab = eligible_slabs.first()
        if not slab:
            return

        incentive_amount = (deal_amount * slab.incentive_percentage) / Decimal('100.0')

        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='topper_month',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Top performer of the month',
            notes=f'Segment: {deal_segment.name}, Slab: ≥ {slab.min_subscription}',
            created_by=self.deal.created_by,
        )

        self.create_payouts(transaction, incentive_amount)

    def process_high_value_deal_incentive(self):
        deal_amount = self.deal.monthlySubscription or 0
        slab = HighValueDealSlab.objects.filter(
            incentive_setup=self.setup,
            min_amount__lte=deal_amount,
            max_amount__gte=deal_amount
        ).first()

        if not slab:
            return

        incentive_amount = (deal_amount * slab.incentive_percentage) / Decimal('100.0')

        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='high_value_deal',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='High value deal incentive matched',
            notes=f'Amount: {deal_amount} Slab: {slab.min_amount}-{slab.max_amount}',
            created_by=self.deal.created_by,
        )

        self.create_payouts(transaction, incentive_amount)

    def create_payouts(self, transaction, incentive_amount):
        payout_split = {
            'dealownerSalesPerson': (transaction.incentive_component_type+'Deal Owner', self.setup.deal_owner),
            'leadSource': (transaction.incentive_component_type+'Lead Source', self.setup.lead_source),
            'followUpSalesPerson': (transaction.incentive_component_type+'Follow Up', self.setup.follow_up),
            'demo1SalesPerson': (transaction.incentive_component_type+'Demo 1', self.setup.demo_1),
            'demo2SalesPerson': (transaction.incentive_component_type+'Demo 2', self.setup.demo_2),
        }

        for field_name, (label, percent) in payout_split.items():
            if not percent:
                continue

            user = getattr(self.deal, field_name, None)

            if user:
                try:
                    PayoutTransaction.objects.create(
                        deal_id=str(self.deal.id),
                        incentive_transaction=transaction,
                        user=user,
                        incentive_person_type=label,
                        payout_amount=(incentive_amount * percent / Decimal('100.0')),
                        payout_status='Pending',
                        payment_method='Bank Transfer',
                        created_by=self.deal.created_by,
                    )
                except Exception as e:
                    print(f"[❌ Error] {label} → Failed to create payout:", e)
            else:
                print(f"[⚠️ No User] {label} → Field '{field_name}' is None in deal.")

    def process_subscription_incentive(self):
        if not all([self.deal.subDate, self.deal.subrenewDate, self.deal.subAmount]):
            return

        if not self.setup:
            return

        sub_amount = self.deal.subAmount
        monthly_target = self.setup.min_subscription_month or 1
        avg_subscription = sub_amount / Decimal(monthly_target)
        percent_achieved = (avg_subscription / self.setup.min_subscription_month) * 100

        if percent_achieved >= 100:
            percentage = self.setup.subscription_100_per_target
        elif percent_achieved >= 75:
            percentage = self.setup.subscription_75_per_target
        elif percent_achieved >= 50:
            percentage = self.setup.subscription_50_per_target
        else:
            percentage = self.setup.subscription_below_50_per

        if not percentage:
            return

        incentive_amount = (sub_amount * percentage) / Decimal('100.0')

    # You can customize this field to another user field if needed
        user = self.deal.dealownerSalesPerson

        from incentives.models import TargetTransaction

        TargetTransaction.objects.create(
            deal=self.deal,
            user=user,
            transaction_type='Earned',
            incentive_component_type='subscription',  # You must add this to the choices
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message=f'Subscription {percent_achieved:.2f}% of target',
            notes=f'Subscription incentive based on ₹{sub_amount} and target {monthly_target} months',
            created_by=self.deal.created_by
        )

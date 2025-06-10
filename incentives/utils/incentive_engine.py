from ..models import (
    Transaction, PayoutTransaction, IncentiveSetup,
    SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget,TargetTransaction,
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
        # financial_year = self.get_current_financial_year()
        financial_year = self.deal.dealWonDate.year
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
        # self.process_subscription_incentive()

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
            deal_id=self.deal,
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

        if self.deal.newMarketPenetration != 'Yes':
            return

        #if not self.setup.new_market_eligibility_months or not self.setup.new_market_deal_incentive:
        #    return

        # client_created_at = getattr(self.deal.clientName, 'created_at', None)
        # if not client_created_at:
        #    return

        # cutoff_date = timezone.now() - relativedelta(months=self.setup.new_market_eligibility_months)
        # if client_created_at > cutoff_date:
        
        incentive_amount = self.setup.new_market_deal_incentive

        transaction = Transaction.objects.create(
            deal_id=self.deal,
            transaction_type='Earned',
            incentive_component_type='new_market',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Client in new market window',
            notes='New Client onboarded on',
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
            deal_id=self.deal,
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
            deal_id=self.deal,
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
        if deal.dealType == 'Domestic':
            payout_split = {
            'Deal Owner': (deal.dealownerSalesPerson, setup.domestic_deal_owner),
            'Lead Source': (deal.leadSource, setup.domestic_lead_source),
            'Follow Up': (deal.followUpSalesPerson, setup.domestic_follow_up),
            'Demo 1': (deal.demo1SalesPerson, setup.domestic_demo_1),
            'Demo 2': (deal.demo2SalesPerson, setup.domestic_demo_2), }
        else:
            payout_split = {
            'Deal Owner': (deal.dealownerSalesPerson, setup.international_deal_owner),
            'Lead Source': (deal.leadSource, setup.international_lead_source),
            'Follow Up': (deal.followUpSalesPerson, setup.international_follow_up),
            'Demo 1': (deal.demo1SalesPerson, setup.international_demo_1),
            'Demo 2': (deal.demo2SalesPerson, setup.international_demo_2), }

        for field_name, (label, percent) in payout_split.items():
            if not percent:
                continue

            try:
                user = getattr(self.deal, field_name)
            except AttributeError:
                print(f"[❌ Error] {label} → Deal does not have the field '{field_name}'")
                continue

            if not user:
                print(f"[⚠️ No User] {label} → Field '{field_name}' is None in deal.")
                continue

            if not isinstance(user, UserProfile):
                print(f"[❌ Error] {label} → Expected UserProfile, got {type(user).__name__}. Field value: {user}")
                continue

            try:
                PayoutTransaction.objects.create(
                    deal=self.deal,
                    incentive_transaction=transaction,
                    user=user,
                    incentive_person_type=label.lower().replace(' ', '_'),  # match your `INCENTIVE_PERSON_CHOICES`
                    payout_amount=(incentive_amount * percent / Decimal('100.0')),
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=self.deal.created_by,
                )
            except Exception as e:
                print(f"[❌ Error] {label} → Failed to create payout: {e}")




    def process_subscription_incentive(self):
        if not all([self.deal.subDate, self.deal.subrenewDate, self.deal.subAmount]):
            return

        if not self.setup:
            return

        sub_amount = self.deal.subAmount

        payout_split = {
            'dealownerSalesPerson': (self.deal.dealownerSalesPerson, 'Deal Owner', self.setup.deal_owner),
            'leadSource': (self.deal.leadSource, 'Lead Source', self.setup.lead_source),
            'followUpSalesPerson': (self.deal.followUpSalesPerson, 'Follow Up', self.setup.follow_up),
            'demo1SalesPerson': (self.deal.demo1SalesPerson, 'Demo 1', self.setup.demo_1),
            'demo2SalesPerson': (self.deal.demo2SalesPerson, 'Demo 2', self.setup.demo_2),
        }

        for field_name, (user, label, percent) in payout_split.items():
            if user and percent:
                try:
                    incentive_amount = (sub_amount * percent) / Decimal('100.0')

                    TargetTransaction.objects.create(
                        deal=self.deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='subscription',
                        amount=incentive_amount,
                        eligibility_status='Eligible',
                        eligibility_message=f'Subscription incentive {percent:.2f}%',
                        notes=f'{label} gets {percent:.2f}% of ₹{sub_amount}',
                        created_by=self.deal.created_by
                    )
                except Exception as e:
                    print(f"[❌ Error] Subscription incentive for {label} → {e}")
            else:
                print(f"[⚠️ Skipped] {label} → Missing user or percent")

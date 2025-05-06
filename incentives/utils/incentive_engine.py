from ..models import (
    Transaction, PayoutTransaction, IncentiveSetup,
    SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget,
    HighValueDealSlab
)
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q
from datetime import timedelta, date


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
            print(f"No IncentiveSetup found for the year {financial_year}.")

    def run_rules(self):
        if not self.setup:
            return
        self.process_setup_incentive()
        self.process_new_market_incentive()
        self.process_topper_month_incentive()
        self.process_high_value_deal_incentive()
        self.process_bifurcation_incentive()
        self.process_setup_charge_slab()

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
            eligibility_message='Matched Setup Slab',
            notes=f'Slab {slab.min_amount}-{slab.max_amount} @ {slab.incentive_percentage}%',
            created_by=self.deal.created_by,
        )

        payout_split = {
            'dealownerSalesPerson': self.setup.deal_owner,
            'lead_source': self.setup.lead_source,
            'follow_up': self.setup.follow_up,
            'demo_1': self.setup.demo_1,
            'demo_2': self.setup.demo_2,
        }

        for person_type, percent in payout_split.items():
            if percent:
                user = getattr(self.deal, person_type, None)
                if user:
                    try:
                        PayoutTransaction.objects.create(
                            deal_id=str(self.deal.id),
                            incentive_transaction=transaction,
                            user=user,
                            incentive_person_type=person_type,
                            payout_amount=(incentive_amount * percent / Decimal('100.0')),
                            payout_status='Pending',
                            payment_method='Bank Transfer',
                            created_by=self.deal.created_by,
                        )
                    except Exception as e:
                        print("Payout creation error:", e)

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

            if self.deal.dealownerSalesPerson:
                try:
                    PayoutTransaction.objects.create(
                        deal_id=str(self.deal.id),
                        incentive_transaction=transaction,
                        user=self.deal.dealownerSalesPerson,
                        incentive_person_type='dealownerSalesPerson',
                        payout_amount=incentive_amount,
                        payout_status='Pending',
                        payment_method='Bank Transfer',
                        created_by=self.deal.created_by,
                    )
                except Exception as e:
                    print("Payout creation error:", e)

    def process_topper_month_incentive(self):
        if not self.setup.enable_topper_1:
            return

        deal_segment = getattr(self.deal, 'segment', None)
        deal_type = getattr(self.deal, 'dealType', 'domestic')
        deal_sub_amount = getattr(self.deal, 'monthlySubscription', 0)

        if not deal_segment or deal_sub_amount <= 0:
            return

        slab = TopperMonthSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_top=deal_type,
            segment=deal_segment,
            min_subscription__lte=deal_sub_amount
        ).order_by('-min_subscription').first()

        if not slab:
            return

        start_of_month = timezone.now().replace(day=1)
        end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(seconds=1)

        top_deal = Deal.objects.filter(
            segment=deal_segment,
            dealType=deal_type,
            monthlySubscription__gt=0,
            status='Approved',
            created_at__range=(start_of_month, end_of_month)
        ).order_by('-monthlySubscription').first()

        if not top_deal or top_deal.id != self.deal.id:
            return

        incentive_amount = (deal_sub_amount * slab.incentive_percentage) / 100

        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='topper_month',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Top performer of the month',
            notes=f'Topper in segment {deal_segment.name}',
            created_by=self.deal.created_by,
        )

        if self.deal.dealownerSalesPerson:
            try:
                PayoutTransaction.objects.create(
                    deal_id=str(self.deal.id),
                    incentive_transaction=transaction,
                    user=self.deal.dealownerSalesPerson,
                    incentive_person_type='dealownerSalesPerson',
                    payout_amount=incentive_amount,
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=self.deal.created_by,
                )
            except Exception as e:
                print("Payout creation error:", e)

    def process_high_value_deal_incentive(self):
        # if not self.setup.enable_high_value_deal:
        #     return

        deal_amount = self.deal.setupCharges or 0
        slab = HighValueDealSlab.objects.filter(
            incentive_setup=self.setup,
            min_amount__lte=deal_amount,
            max_amount__gte=deal_amount
        ).first()

        if not slab:
            return

        incentive_amount = (deal_amount * slab.incentive_percentage) / 100

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

        if self.deal.dealownerSalesPerson:
            try:
                PayoutTransaction.objects.create(
                    deal_id=str(self.deal.id),
                    incentive_transaction=transaction,
                    user=self.deal.dealownerSalesPerson,
                    incentive_person_type='dealownerSalesPerson',
                    payout_amount=incentive_amount,
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=self.deal.created_by,
                )
            except Exception as e:
                print("Payout creation error:", e)

    def process_bifurcation_incentive(self):
        # if not self.setup.enable_bifurcation_incentive:
        #     return

        total_amount = self.deal.setupCharges or 0
        if total_amount <= 0:
            return

    # Mapping role to (UserProfile instance, percentage from setup)
        bifurcation_data = {
            'deal_owner': (self.deal.dealownerSalesPerson, self.setup.deal_owner),
            'lead_source': (self.deal.leadSource, self.setup.lead_source),
            'follow_up': (self.deal.followUpSalesPerson, self.setup.follow_up),
            'demo_1': (self.deal.demo1SalesPerson, self.setup.demo_1),
            'demo_2': (self.deal.demo2SalesPerson, self.setup.demo_2),
        }

        total_percentage = sum(p for (_, p) in bifurcation_data.values() if p)
        if total_percentage <= 0:
            return

        total_incentive_amount = (total_amount * total_percentage) / 100

    # Create summary transaction
        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='bifurcation',
            amount=total_incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Bifurcation incentive applied',
            notes='Based on bifurcation slab from IncentiveSetup',
            created_by=self.deal.created_by,
        )

    # Distribute individual payouts
        for role, (user, percentage) in bifurcation_data.items():
            if user and percentage and percentage > 0:
                PayoutTransaction.objects.create(
                    deal_id=str(self.deal.id),
                    incentive_transaction=transaction,
                    user=user,
                    incentive_person_type=role,
                    payout_amount=(total_amount * percentage / 100),
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=self.deal.created_by,
                )



    def process_setup_charge_slab(self):
        deal_amount = self.deal.setupCharges
        dealType = self.deal.dealType.lower()  # Assuming 'domestic' or 'international'

        # Find the matching setup charge slab
        slab = SetupChargeSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_setup=dealType,
            min_amount__lte=deal_amount,
            max_amount__gte=deal_amount
        ).first()

        if not slab:
            return  # No matching incentive slab

        # Calculate incentive based on the slab
        incentive_amount = (deal_amount * slab.incentive_percentage) / Decimal('100.0')

        # Create a Transaction for the incentive
        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='setup_charge_slab',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message=f'Matched Setup Charge Slab ({slab.min_amount} - {slab.max_amount})',
            notes=f'Slab {slab.min_amount}-{slab.max_amount} @ {slab.incentive_percentage}%',
            created_by=self.deal.created_by,
        )

        # Optional: Bifurcate the payout among the participants, if necessary
        payout_split = {
            'dealownerSalesPerson': self.setup.deal_owner,
            'lead_source': self.setup.lead_source,
            'follow_up': self.setup.follow_up,
            'demo_1': self.setup.demo_1,
            'demo_2': self.setup.demo_2,
        }

        for person_type, percent in payout_split.items():
            if not percent:
                continue
            user = getattr(self.deal, person_type, None)
            if user:
                try:
                    payout = PayoutTransaction.objects.create(
                    deal_id=str(self.deal.id),
                    incentive_transaction=transaction,
                    user=user,
                    incentive_person_type=person_type,
                    payout_amount=(incentive_amount * percent / Decimal('100.0')),
                    payout_status='Pending',
                    payment_method='Bank Transfer',  # default
                    created_by=self.deal.created_by,
                 )
                except Exception as e:
                    print("Payout creation error:", e)



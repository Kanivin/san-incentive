from ..models import (Transaction, PayoutTransaction, IncentiveSetup,
                      SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget,
                      HighValueDealSlab)
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, F, Q
from django.utils.timezone import now
from calendar import monthrange
from datetime import timedelta, date

class DealRuleEngine:

    def __init__(self, deal):
        self.deal = deal
        # Initialize the setup object
        self.setup = None
        self.initialize_setup()

    # Helper function to get current financial year
    def get_current_financial_year(self):
        current_date = date.today()
        if current_date.month < 4:
            start_year = current_date.year - 1
        else:
            start_year = current_date.year
        return f"{start_year}-{start_year + 1}"

    # Initialize setup based on current financial year
    def initialize_setup(self):
        current_financial_year = self.get_current_financial_year()
        self.setup = IncentiveSetup.objects.filter(financial_year=current_financial_year).last()

        if self.setup:
            print(f"Financial Year: {self.setup.financial_year}")
        else:
            print("No IncentiveSetup found for the current financial year.")

    def run_rules(self):
        if not self.setup:
            return  # No rule setup defined for this year

        # Call each of the incentive processing methods
        self.process_setup_incentive()
        self.process_new_market_incentive()
        self.process_topper_month_incentive()
        self.process_high_value_deal_incentive()
        self.process_bifurcation_incentive()
        self.process_setup_charge_slab()

    def process_setup_incentive(self):
        deal_amount = self.deal.setupCharges
        dealType = self.deal.dealType.lower(
        )  # Assuming 'domestic' or 'international'

        # Find matching setup slab
        slab = SetupChargeSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_setup=dealType,
            min_amount__lte=deal_amount,
            max_amount__gte=deal_amount).first()

        if not slab:
            return  # No matching incentive slab

        # Calculate incentive amount
        incentive_amount = (deal_amount *
                            slab.incentive_percentage) / Decimal('100.0')

        # Create Transaction
        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='setup',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message='Matched Setup Slab',
            notes=
            f'Slab {slab.min_amount}-{slab.max_amount} @ {slab.incentive_percentage}%',
            created_by=self.deal.
            created_by,  # Assuming AuditMixin handles this
        )

        # Bifurcate payouts
        payout_split = {
            'dealownerSalesPerson': self.setup.dealownerSalesPerson,
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
                    payout_amount=(incentive_amount * percent /
                                   Decimal('100.0')),
                    payout_status='Pending',
                    payment_method='Bank Transfer',  # default
                    created_by=self.deal.created_by,
                    )
                except Exception as e:
                    print("Payout creation error:", e)

    def process_new_market_incentive(self):
        if not self.setup.new_market_eligibility_months or not self.setup.new_market_deal_incentive:
            return  # Rule not active

        client_created_at = getattr(self.deal.clientName, 'created_at', None)
        if not client_created_at:
            return

        # Check eligibility
        cutoff_date = timezone.now() - relativedelta(
            months=self.setup.new_market_eligibility_months)
        if client_created_at > cutoff_date:
            # Eligible for new market incentive
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

        # Optional: Add a single payout (e.g., to Deal Owner)
        if self.deal.dealownerSalesPerson:
            try:
                PayoutTransaction.objects.create(
                deal_id=str(self.deal.id),
                incentive_transaction=transaction,
                user=self.deal.dealownerSalesPerson,
                incentive_person_type='deal ownern',
                payout_amount=incentive_amount,
                payout_status='Pending',
                payment_method='Bank Transfer',
                created_by=self.deal.created_by,
                )
            except Exception as e:
                    print("Payout creation error:", e)

    def process_topper_month_incentive(self):
        if not self.setup.enable_topper_1:
            return  # Rule not active

        deal_segment = getattr(self.deal, 'segment', None)
        dealType = getattr(self.deal, 'dealType', 'domestic')
        deal_sub_amount = getattr(self.deal, 'monthlySubscription', 0)

        if not deal_segment or deal_sub_amount <= 0:
            return

        # Get slab for this segment and type
        slab = TopperMonthSlab.objects.filter(
            incentive_setup=self.setup,
            dealType_top=dealType,
            segment=deal_segment,
            min_subscription__lte=deal_sub_amount).order_by(
                '-min_subscription').first()

        if not slab:
            return

        # Find top performer of the month in the same segment
        start_of_month = timezone.now().replace(day=1)
        end_of_month = (start_of_month +
                        relativedelta(months=1)) - timedelta(seconds=1)

        top_deal = Deal.objects.filter(
            segment=deal_segment,
            dealType=dealType,
            monthlySubscription__isnull=False,
            monthlySubscription__gt=0,
            status='Approved',
            created_at__range=(
                start_of_month,
                end_of_month)).order_by('-monthlySubscription').first()

        if not top_deal or top_deal.id != self.deal.id:
            return  # Not the top performer

        # Calculate and create transaction
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

        # Optional payout to dealownerSalesPerson
        if self.deal.dealownerSalesPerson:
            try:
                PayoutTransaction.objects.create(
                deal_id=str(self.deal.id),
                incentive_transaction=transaction,
                user=self.deal.dealownerSalesPerson,
                incentive_person_type='deal ownern',
                payout_amount=incentive_amount,
                payout_status='Pending',
                payment_method='Bank Transfer',
                created_by=self.deal.created_by,
                )
            except Exception as e:
                    print("Payout creation error:", e)

    

    # def process_annual_target_incentive(self):
    #     # Step 1: Get AnnualTarget record
    #     try:
    #         target = AnnualTarget.objects.get(
    #             user=self.deal.dealownerSalesPerson,
    #             financial_year=self.setup.financial_year)
    #     except AnnualTarget.DoesNotExist:
    #         return

    #     if not target.target_amount or target.target_amount <= 0:
    #         return

    # # Step 2: Calculate achievement %
    #     achieved_percent = (target.achieved_amount /
    #                         target.target_amount) * 100

    #     # Step 3: Match with Incentive Slab
    #     incentive_percent = None
    #     message = None

    #     if achieved_percent >= 100 and self.setup.enable_above_100_achievement:
    #         incentive_percent = self.setup.subscription_100_per_target
    #         message = "Achieved above 100% of target"
    #     elif 95 <= achieved_percent < 100 and self.setup.enable_95_100_achievement:
    #         incentive_percent = self.setup.subscription_100_per_target
    #         message = "Achieved between 95%-100%"
    #     elif 90 <= achieved_percent < 95 and self.setup.enable_90_95_achievement:
    #         incentive_percent = self.setup.subscription_75_per_target
    #         message = "Achieved between 90%-95%"
    #     elif 75 <= achieved_percent < 90 and self.setup.enable_75_90_achievement:
    #         incentive_percent = self.setup.subscription_50_per_target
    #         message = "Achieved between 75%-90%"
    #     elif achieved_percent < 75 and self.setup.enable_minimum_benchmark:
    #         incentive_percent = self.setup.subscription_below_50_per
    #         message = "Achieved less than 75%"

    #     if incentive_percent is None:
    #         return

    # # Step 4: Calculate incentive
    #     incentive_amount = (target.achieved_amount * incentive_percent) / 100

    #     # Step 5: Record transaction
    #     transaction = Transaction.objects.create(
    #         deal_id=str(self.deal.id),
    #         transaction_type='Earned',
    #         incentive_component_type='subscription_target',
    #         amount=incentive_amount,
    #         eligibility_status='Eligible',
    #         eligibility_message=message,
    #         notes=f'Based on {achieved_percent:.2f}% target achieved',
    #         created_by=self.deal.created_by,
    #     )

    #     # Step 6: Payout to the owner
    #     if self.deal.dealownerSalesPerson:
    #         PayoutTransaction.objects.create(
    #             deal_id=str(self.deal.id),
    #             incentive_transaction=transaction,
    #             user=self.deal.dealownerSalesPerson,
    #             incentive_person_type='deal ownern',
    #             payout_amount=incentive_amount,
    #             payout_status='Pending',
    #             payment_method='Bank Transfer',
    #             created_by=self.deal.created_by,
    #         )


    def process_topper_month_incentive(self):
        if not self.setup.enable_topper_1:
            return

        # Get deal month range
        deal_month_start = self.deal.created_at.replace(day=1)
        last_day = monthrange(self.deal.created_at.year,
                            self.deal.created_at.month)[1]
        deal_month_end = self.deal.created_at.replace(day=last_day)

        # Aggregate total subscription per user in the same segment and month
        user_totals = (Deal.objects.filter(
            created_at__range=(deal_month_start, deal_month_end),
            segment=self.deal.segment,
            dealType=self.deal.dealType,
            status='Won').values('dealownerSalesPerson').annotate(
                total_sub=Sum('monthlySubscription')).order_by('-total_sub'))

        if not user_totals:
            return

    # Identify top user (and optionally 2nd if enabled)
        top_user = user_totals[0]
        second_user = user_totals[1] if len(user_totals) > 1 else None

        current_user_id = self.deal.dealownerSalesPerson.id if self.deal.dealownerSalesPerson else None
        if not current_user_id:
            return

        is_topper = current_user_id == top_user['dealownerSalesPerson']
        is_second_topper = second_user and current_user_id == second_user[
            'dealownerSalesPerson']

    # Fetch relevant slab
        slab_qs = TopperMonthSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_top=self.deal.dealType,
            segment=self.deal.segment,
        )

    # Determine incentive
        applicable_slab = slab_qs.first()
        if not applicable_slab:
            return

        if is_topper and self.setup.enable_topper_1:
            incentive_percent = applicable_slab.incentive_percentage
            title = "Topper of the Month - 1st"
        elif is_second_topper and self.setup.enable_topper_2:
            incentive_percent = applicable_slab.incentive_percentage / 2  # or another logic
            title = "Topper of the Month - 2nd"
        else:
            return

        incentive_amount = (self.deal.monthlySubscription *
                        incentive_percent) / 100

        # Create transaction
        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='topper_of_month',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message=title,
            notes=f'Incentive for {title} in {self.deal.segment.name}',
            created_by=self.deal.created_by,
        )
        try:
           PayoutTransaction.objects.create(
            deal_id=str(self.deal.id),
            incentive_transaction=transaction,
            user=self.deal.dealownerSalesPerson,
            incentive_person_type='deal ownern',
            payout_amount=incentive_amount,
            payout_status='Pending',
            payment_method='Bank Transfer',
            created_by=self.deal.created_by,
          )
        except Exception as e:
                    print("Payout creation error:", e)

    def process_high_value_deal_incentive(self):
        # Fetch matching slabs for the current deal
        slabs = HighValueDealSlab.objects.filter(
            incentive_setup=self.setup,
            deal_type_high=self.deal.dealType,
            min_amount__lte=self.deal.setupCharges,
            max_amount__gte=self.deal.setupCharges).order_by('min_amount')

        if not slabs.exists():
            return

    # Pick the most appropriate slab (should be only one)
        slab = slabs.first()
        incentive_percent = slab.incentive_percentage
        incentive_amount = (self.deal.setupCharges * incentive_percent) / 100

    # Create transaction
        transaction = Transaction.objects.create(
            deal_id=str(self.deal.id),
            transaction_type='Earned',
            incentive_component_type='high_value_deal',
            amount=incentive_amount,
            eligibility_status='Eligible',
            eligibility_message=
            f"High Value Deal Slab {slab.min_amount}-{slab.max_amount}",
            notes=
            f"Incentive for high value deal in range {slab.min_amount}-{slab.max_amount}",
            created_by=self.deal.created_by,
        )
        try:
            PayoutTransaction.objects.create(
            deal_id=str(self.deal.id),
            incentive_transaction=transaction,
            user=self.deal.dealownerSalesPerson,
            incentive_person_type='deal ownern',
            payout_amount=incentive_amount,
            payout_status='Pending',
            payment_method='Bank Transfer',
            created_by=self.deal.created_by,
            )
        except Exception as e:
                    print("Payout creation error:", e)


    # def process_new_market_incentive(self):
    #     customer = self.deal.clientName
    #     deal_date = self.deal.created_at
    #     customer_created = customer.created_at

    # # Rule parameters
    #     eligibility_months = self.setup.new_market_eligibility_months
    #     fixed_incentive = self.setup.new_market_deal_incentive

    #     if not (eligibility_months and fixed_incentive and customer_created):
    #         return  # Config missing or data invalid

    #     month_delta = timedelta(days=eligibility_months * 30)
    #     is_eligible = (deal_date - customer_created) <= month_delta

    #     if not is_eligible:
    #         return

    #     transaction = Transaction.objects.create(
    #         deal_id=str(self.deal.id),
    #         transaction_type='Earned',
    #         incentive_component_type='new_market',
    #         amount=fixed_incentive,
    #         eligibility_status='Eligible',
    #         eligibility_message=
    #         f"Customer within {eligibility_months} months of registration",
    #         notes=f"New Market Incentive of ₹{fixed_incentive}",
    #         created_by=self.deal.created_by,
    #     )

    # # Default payout to deal owner (customize if needed)
    #     if self.deal.dealownerSalesPerson:
    #         PayoutTransaction.objects.create(
    #             deal_id=str(self.deal.id),
    #             incentive_transaction=transaction,
    #             user=self.deal.dealownerSalesPerson,
    #             incentive_person_type='deal ownern',
    #             payout_amount=fixed_incentive,
    #             payout_status='Pending',
    #             payment_method='Bank Transfer',
    #             created_by=self.deal.created_by,
    #      )

    def process_bifurcation_incentive(self):

        deal_amount = self.deal.setupCharges

        if deal_amount <= 0:
            return

        bifurcation_split = {
            'dealownerSalesPerson': self.setup.deal_owner,
            'lead_source': self.setup.lead_source,
            'follow_up': self.setup.follow_up,
            'demo_1': self.setup.demo_1,
            'demo_2': self.setup.demo_2,
        }

        total_bifurcation_percentage = sum(percent for percent in bifurcation_split.values() if percent)

        if total_bifurcation_percentage != 100:
            return

        for person_type, percent in bifurcation_split.items():
            if not percent:
                continue

            user = getattr(self.deal, person_type, None)
            if user:
                payout_amount = (deal_amount * percent) / Decimal('100.0')

                transaction = Transaction.objects.create(
                    deal_id=str(self.deal.id),
                    transaction_type='Earned',
                    incentive_component_type='bifurcation',
                    amount=payout_amount,
                    eligibility_status='Eligible',
                    eligibility_message=f'Bifurcation - {person_type}',
                    notes=f'Payout for {person_type} based on {percent}%',
                    created_by=self.deal.created_by,
                )
                try:
                    PayoutTransaction.objects.create(
                    deal_id=str(self.deal.id),
                    incentive_transaction=transaction,
                    user=user,
                    incentive_person_type=person_type,
                    payout_amount=payout_amount,
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=self.deal.created_by,
                    )
                except Exception as e:
                    print("Payout creation error:", e)

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
            'dealownerSalesPerson': self.setup.dealownerSalesPerson,
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



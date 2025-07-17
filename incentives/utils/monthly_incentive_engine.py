from collections import defaultdict
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import calendar

from ..models import (
    Transaction, PayoutTransaction, IncentiveSetup,
    SetupChargeSlab, TopperMonthSlab, Deal, AnnualTarget, TargetTransaction,Segment,
    HighValueDealSlab, UserProfile
)


class MonthlyRuleEngine:

    def __init__(self, run_month):
        self.run_month = run_month
        self.run_month_name = calendar.month_name[self.run_month]
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
        user_setup_tracker = set() 

        for deal in self.deals_in_month:
            user_split = self.get_payout_split(deal)  # Returns {Role: (User, %)}
            segment_id = deal.segment.id if deal.segment else None
            setup_charges_amount = Decimal(deal.setupCharges or 0)
            monthly_subscription_amount = Decimal(deal.monthlySubscription or 0)
                        
            for role, (user, percent) in user_split.items():
                if not user or percent is None:
                    continue

                deal_key = (user.id, deal.id, role)
                if deal_key in user_deal_tracker:
                    continue  # Avoid double-counting same user-role-deal

                # Skip admin Deal Owner and deduct their setup charge portion
                if  user.user_type and user.user_type.name.lower() == "admin":
                    admin_percent = Decimal(percent or 0)
                    setup_charges_deduction = setup_charges_amount * admin_percent / 100
                    setup_charges_amount -= setup_charges_deduction
                    print(f"[INFO] Skipped admin Lead Source ({user.id}), reduced setupChargesAmount by {setup_charges_deduction}")
                    continue

                # Accumulate setup charges once per user — if you want to count this per role, move inside the role loop
                setup_key = (user.id, deal.id)
                if setup_key not in user_setup_tracker:
                    user_setup_totals[user.id] += setup_charges_amount
                    user_setup_tracker.add(setup_key)

                # Add subscription share
                subscription_share = monthly_subscription_amount * Decimal(percent) / 100
                subscription_key = (user.id, segment_id)
                user_monthly_subscription_totals[subscription_key] += subscription_share

                print(f"monthly_subscription_amount is {monthly_subscription_amount} , percent is {percent} , subscription_key is {subscription_key}  , subscription_share is  {subscription_share}")
               
                # Mark this user-role-deal as processed
                user_deal_tracker.add(deal_key)

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
                   self.process_high_value_incentive(deal, payout_split, monthly_subscription_charges)
                if deal.newMarketPenetration == 'Yes':
                    self.process_new_market_incentive(deal, payout_split)
                # Mark as executed after successful processing
                deal.monthly_rule_executed = True
                deal.save(update_fields=['monthly_rule_executed'])
            except Exception as e:
                # Optional: log or handle the error without stopping the loop
                print(f"[ERROR] Skipping deal {deal.id} due to: {e}")

        self.process_topper_incentive(user_monthly_subscription_totals)
                    
    def get_payout_split(self, deal):
        if deal.dealType == 'domestic':
            return {
                'Lead Source': (deal.leadSource, self.setup.domestic_lead_source),
                'Deal Owner': (deal.dealownerSalesPerson, self.setup.domestic_deal_owner),                
                'Follow Up': (deal.followUpSalesPerson, self.setup.domestic_follow_up),
                'Demo 1': (deal.demo1SalesPerson, self.setup.domestic_demo_1),
                'Demo 2': (deal.demo2SalesPerson, self.setup.domestic_demo_2),
            }
        return {
            'Lead Source': (deal.leadSource, self.setup.international_lead_source),
            'Deal Owner': (deal.dealownerSalesPerson, self.setup.international_deal_owner),            
            'Follow Up': (deal.followUpSalesPerson, self.setup.international_follow_up),
            'Demo 1': (deal.demo1SalesPerson, self.setup.international_demo_1),
            'Demo 2': (deal.demo2SalesPerson, self.setup.international_demo_2),
        }

    def process_setup_incentive(self, deal, payout_split, deal_type, setup_charges, user_setup_totals):
        for label, (user, percent) in payout_split.items():
            label_with_tag = f"{label}(Setup)"
            if user and percent:
                try:

                    if user.user_type and user.user_type.name.lower() == "admin":
                        print(f"[Warning] user.user_type.name.lower()  is {user.user_type.name.lower() }. Skipping...") 
                        continue

                    total_user_amount = user_setup_totals.get(user.id, Decimal('0.00'))
                    
                    # Actual matching slab  
                    matching_slab = SetupChargeSlab.objects.filter(
                        incentive_setup=self.setup,
                        deal_type_setup=deal_type
                    ).order_by('min_amount').first()

                    if not matching_slab:
                        continue

                    lowest_slab = matching_slab    
                               
                    if total_user_amount <= lowest_slab.max_amount:
                        # Less than all slabs — use lowest slab
                        slab_percentage = lowest_slab.incentive_percentage
                    else:
                        slab = SetupChargeSlab.objects.filter(
                        incentive_setup=self.setup,
                        deal_type_setup=deal_type,
                        min_amount__lte=setup_charges,
                        max_amount__gte=setup_charges
                         ).first()

                        if slab: 
                            slab_percentage = slab.incentive_percentage
                        else:    
                            slab_percentage = lowest_slab.incentive_percentage

                    incentive_amount = (setup_charges * slab_percentage) / Decimal('100.0')
                    incentive_amount_user = (incentive_amount * percent) / Decimal('100.0')

                    transaction = Transaction.objects.create(
                        deal_id=deal,
                        user=user,
                        transaction_type='Earned',
                        incentive_component_type='setup',
                        amount=incentive_amount_user,
                        eligibility_status='Eligible',
                        eligibility_message='Matched Setup Charge Slab',
                        notes=f'Slab @ {slab_percentage}%',
                        created_by="system-mjob"
                    )
                    self.create_payouts(deal, transaction, user, label_with_tag, incentive_amount_user)
                except Exception as e:
                    print(f"[ERROR] Processing {label} for deal {deal.id} → {e}")
            else:
                print(f"[INFO] Skipped {label} → Missing user or percent")

    def process_topper_incentive(self, user_monthly_subscription_totals):
        topper_by_segment = dict()

        # 1. Group totals by segment
        segment_user_totals = defaultdict(list)
        for (user_id, segment_id), total in user_monthly_subscription_totals.items():
            segment_user_totals[segment_id].append((user_id, total))

        # 2. Find the top user for each segment
        for segment_id, user_totals in segment_user_totals.items():
            if user_totals:
                top_user = max(user_totals, key=lambda x: x[1])
                topper_by_segment[segment_id] = {
                    "user_id": top_user[0],
                    "total_subscription": top_user[1]
                }

        # 3. Process incentives
        for segment_id, topper_info in topper_by_segment.items():
            try:
                user_id = topper_info["user_id"]
                total_user_amount = topper_info["total_subscription"]
                user = UserProfile.objects.get(id=user_id)
                segment = Segment.objects.get(id=segment_id) if segment_id else None

                # Determine applicable slab (deal_type logic can be extended)
                slab = TopperMonthSlab.objects.filter(
                    incentive_setup=self.setup,
                    deal_type_top__in=['all'],  # Add 'domestic'/'international' as needed
                    segment=segment,
                    min_subscription__lte=total_user_amount
                ).order_by('-min_subscription').first()

                if not slab:
                    continue

                percent = slab.incentive_percentage
                incentive_amount = total_user_amount * percent / Decimal(100)

                transaction = Transaction.objects.create(
                    user=user,
                    deal_id=None,
                    transaction_type='Earned',
                    incentive_component_type='topper_month',
                    amount=incentive_amount,
                    eligibility_status='Eligible',
                    eligibility_message='Top performer of the month',
                    notes=f"Segment: {segment.name if segment else 'N/A'}, Slab: ≥ {slab.min_subscription}",
                    created_by="system-mjob"
                )

                PayoutTransaction.objects.create(
                    incentive_transaction=transaction,
                    user=user,
                    deal=None,
                    incentive_person_type=f'{self.run_month_name} Month Top Performer ({segment.name if segment else "N/A"})',
                    payout_amount=incentive_amount,
                    payout_status='ReadyToPay',
                    payment_method='Bank Transfer',
                    created_by="system-mjob"
                )

            except Exception as e:
                print(f"[ERROR] Processing topper for segment ID {segment_id} → {e}")
            

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
        user = deal.dealownerSalesPerson

        if user:
            try:
                transaction = Transaction.objects.create(
                    deal_id=deal,
                    user=user,
                    transaction_type='Earned',
                    incentive_component_type='new_market',
                    amount=incentive_amount,
                    eligibility_status='Eligible',
                    eligibility_message='Client in new market window',
                    notes='New Client onboarded',
                    created_by="system-mjob"
                )
                self.create_payouts(deal, transaction, user, "Deal Owner(New Market)", incentive_amount)
            except Exception as e:
                print(f"[ERROR] Processing New Market for deal {deal.id} → {e}")
        else:
            print(f"[INFO] Skipped New Market → Missing Deal Owner")

    def process_new_market_incentive_old(self, deal, payout_split):
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
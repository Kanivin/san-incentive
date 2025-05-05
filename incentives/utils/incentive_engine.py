from ..models import Transaction
from ..models import SetupChargeSlab, HighValueDealSlab, TopperMonthSlab
from ..utils import process_deal_incentives  # Handles bifurcation
from decimal import Decimal


class DealRuleEngine:
    def __init__(self, deal):
        self.deal = deal
        self.deal_info = self.extract_deal_info()
        self.setup_charge_slabs = self.get_setup_slabs()
        self.high_value_slabs = self.get_high_value_slabs()
        self.topper_charge_slabs = self.get_topper_slabs()
        self.new_market_status = self.check_new_market()
        self.deal_roles = self.get_deal_roles()

    def run_rules(self):
        self.fact_check()
        self.condition_check()

    def fact_check(self):
        setup_amount = self.deal.setupCharges
        subscription_amount = self.deal.monthlySubscription
        segment = self.deal.segment

        # Calculate incentives
        setup_incentive = calculate_setup_incentive(setup_amount, self.setup_charge_slabs)
        high_value_incentive = calculate_high_value_incentive(subscription_amount, self.high_value_slabs)
        topper_incentive = calculate_topper_incentive(segment, subscription_amount, self.topper_charge_slabs)
        new_market_incentive = calculate_new_market_incentive(self.new_market_status)

        # Insert records
        user = self.deal.updated_by  # Use audit mixin info
        create_incentive_transaction(self.deal.id, 'setup', setup_incentive, user)
        create_incentive_transaction(self.deal.id, 'high_value', high_value_incentive, user)
        create_incentive_transaction(self.deal.id, 'topper_month', topper_incentive, user)
        create_incentive_transaction(self.deal.id, 'new_market', new_market_incentive, user)

    def condition_check(self):
        bifurcation_slabs = self.get_bifurcation_slabs()
        process_deal_incentives(self.deal_info, bifurcation_slabs)

    # ---------------- Helper Methods ----------------

    def get_setup_slabs(self):
        return SetupChargeSlab.objects.all()

    def get_high_value_slabs(self):
        return HighValueDealSlab.objects.all()

    def get_topper_slabs(self):
        return TopperMonthSlab.objects.all()

    def check_new_market(self):
        return self.deal.newMarketPenetration == 'Yes'

    def get_deal_roles(self):
        return {
            "deal_source": self.deal.leadSource_id,
            "deal_owner": self.deal.dealownerSalesPerson_id,
            "follow_up": self.deal.followUpSalesPerson_id,
            "demo_1": self.deal.demo1SalesPerson_id,
            "demo_2": self.deal.demo2SalesPerson_id,
        }

    def extract_deal_info(self):
        return {
            "deal_id": self.deal.id,
            "setup_amount": self.deal.setupCharges,
            "subscription_amount": self.deal.monthlySubscription,
            "segment": self.deal.segment.name if self.deal.segment else None,
            "is_new_market": self.check_new_market(),
            "roles": self.get_deal_roles(),
        }

    def get_bifurcation_slabs(self):
        # Placeholder: you can query slabs based on dealType/segment
        from ..models import BifurcationSlab
        return BifurcationSlab.objects.filter(segment=self.deal.segment)


# ------------------ Incentive Calculation ------------------

def calculate_setup_incentive(setup_amount, setup_charge_slabs):
    for slab in setup_charge_slabs:
        if slab.min_amount <= setup_amount <= slab.max_amount:
            return round(setup_amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_high_value_incentive(subscription_amount, high_value_slabs):
    for slab in high_value_slabs:
        if slab.min_amount <= subscription_amount <= slab.max_amount:
            return round(subscription_amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_topper_incentive(segment, subscription_amount, topper_charge_slabs):
    for slab in topper_charge_slabs:
        if slab.segment == segment and subscription_amount >= slab.min_subscription:
            return round(subscription_amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_new_market_incentive(is_new_market_status):
    NEW_MARKET_FIXED_INCENTIVE = Decimal('1000.00')
    return NEW_MARKET_FIXED_INCENTIVE if is_new_market_status else Decimal('0.00')


def create_incentive_transaction(deal_id, component_type, amount, user):
    if amount > 0:
        Transaction.objects.create(
            deal_id=deal_id,
            transaction_type='Earned',
            incentive_component_type=component_type,
            amount=amount,
            created_by=user,
            updated_by=user
        )

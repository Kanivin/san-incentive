import logging
from decimal import Decimal

from ..models import (
    Transaction,
    SetupChargeSlab,
    HighValueDealSlab,
    TopperMonthSlab,
    IncentiveSetup
)
from ..utils.process_deal_incentives import process_deal_incentives

logger = logging.getLogger(__name__)

VALID_COMPONENTS = ['setup', 'new_market', 'topper_month', 'single_high']


class DealRuleEngine:
    def __init__(self, deal):
        self.deal = deal
        self.deal_info = self.extract_deal_info()
        self.setup_charge_slabs = self.get_setup_slabs()
        self.high_value_slabs = self.get_high_value_slabs()
        self.topper_charge_slabs = self.get_topper_slabs()
        self.is_new_market = self.check_new_market()
        self.deal_roles = self.get_deal_roles()

    def run_rules(self):
        self.fact_check()
        self.condition_check()

    def fact_check(self):
        setup_amount = self.deal.setupCharges or Decimal('0.00')
        subscription_amount = self.deal.monthlySubscription or Decimal('0.00')
        segment = self.deal.segment.name if self.deal.segment else None
        user = self.deal.updated_by

        setup_incentive = calculate_setup_incentive(setup_amount, self.setup_charge_slabs)
        high_value_incentive = calculate_high_value_incentive(subscription_amount, self.high_value_slabs)
        topper_incentive = calculate_topper_incentive(segment, subscription_amount, self.topper_charge_slabs)
        new_market_incentive = calculate_new_market_deal_incentive(self.is_new_market)

        create_incentive_transaction(self.deal.id, 'setup', setup_incentive, user)
        create_incentive_transaction(self.deal.id, 'single_high', high_value_incentive, user)
        create_incentive_transaction(self.deal.id, 'topper_month', topper_incentive, user)
        create_incentive_transaction(self.deal.id, 'new_market', new_market_incentive, user)

    def condition_check(self):
        incentive_setup = self.get_bifurcation_slabs()
        if not incentive_setup:
            logger.warning("No IncentiveSetup found for bifurcation")
            return

        bifurcation = {
            "deal_owner": incentive_setup.deal_owner or Decimal('0.00'),
            "lead_source": incentive_setup.lead_source or Decimal('0.00'),
            "follow_up": incentive_setup.follow_up or Decimal('0.00'),
            "demo_1": incentive_setup.demo_1 or Decimal('0.00'),
            "demo_2": incentive_setup.demo_2 or Decimal('0.00'),
        }

        process_deal_incentives(self.deal_info, bifurcation)

    # ---------------- Helper Methods ----------------

    def get_setup_slabs(self):
        return SetupChargeSlab.objects.all()

    def get_high_value_slabs(self):
        return HighValueDealSlab.objects.all()

    def get_topper_slabs(self):
        return TopperMonthSlab.objects.select_related('segment').all()

    def check_new_market(self):
        return self.deal.newMarketPenetration == 'Yes'

    def get_deal_roles(self):
        return {
            "lead_source": self.deal.leadSource_id,
            "deal_owner": self.deal.dealownerSalesPerson_id,
            "follow_up": self.deal.followUpSalesPerson_id,
            "demo_1": self.deal.demo1SalesPerson_id,
            "demo_2": self.deal.demo2SalesPerson_id,
        }

    def extract_deal_info(self):
        return {
            "deal_id": self.deal.id,
            "setup_amount": self.deal.setupCharges or Decimal('0.00'),
            "subscription_amount": self.deal.monthlySubscription or Decimal('0.00'),
            "segment": self.deal.segment.name if self.deal.segment else None,
            "is_new_market": self.check_new_market(),
            "roles": self.get_deal_roles(),
        }

   def get_bifurcation_slabs():
    setup = IncentiveSetup.objects.prefetch_related(
        'setup_slabs', 'topper_slabs', 'high_value_slabs'
    ).first()
    
    if not setup:
        return {}

    # Bifurcation for general setup components
    setup_bifurcation = {
        "deal_owner": float(setup.deal_owner or 0),
        "lead_source": float(setup.lead_source or 0),
        "follow_up": float(setup.follow_up or 0),
        "demo_1": float(setup.demo_1 or 0),
        "demo_2": float(setup.demo_2 or 0),
    }

    # Optional: logic to get slab-based bifurcations for single_high or topper_month
    # These usually have more dynamic structure depending on business logic
    high_value_bifurcation = {}
    for slab in setup.high_value_slabs.all():
        key = f"{slab.deal_type_high}_{slab.min_amount}_{slab.max_amount}"
        high_value_bifurcation[key] = {
            "deal_owner": 100  # Assuming full goes to deal_owner unless further role mapping
        }

    topper_month_bifurcation = {
        "demo_1": float(setup.demo_1 or 0),
        "demo_2": float(setup.demo_2 or 0)
    }

    # New market assumed to go fully to deal_owner unless changed
    new_market_bifurcation = {
        "deal_owner": 100.0
    }

    return {
        "setup": setup_bifurcation,
        "single_high": high_value_bifurcation.get("domestic_0.00_999999.99", setup_bifurcation),  # fallback
        "topper_month": topper_month_bifurcation,
        "new_market": new_market_bifurcation
    }



# ------------------ Incentive Calculation ------------------

def calculate_setup_incentive(amount, slabs):
    for slab in slabs:
        if slab.min_amount <= amount <= slab.max_amount:
            return round(amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_high_value_incentive(amount, slabs):
    for slab in slabs:
        if slab.min_amount <= amount <= slab.max_amount:
            return round(amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_topper_incentive(segment, amount, slabs):
    if not segment:
        return Decimal('0.00')
    for slab in slabs:
        if slab.segment.name == segment and amount >= slab.min_subscription:
            return round(amount * (slab.incentive_percentage / Decimal('100.0')), 2)
    return Decimal('0.00')


def calculate_new_market_deal_incentive(is_new_market):
    try:
        setup = IncentiveSetup.objects.first()
        return setup.new_market_deal_incentive if (setup and is_new_market) else Decimal('0.00')
    except IncentiveSetup.DoesNotExist:
        logger.warning("IncentiveSetup not found for new market incentive.")
        return Decimal('0.00')


# ------------------ Transaction Handler ------------------

def create_incentive_transaction(deal_id, component_type, amount, user):
    try:
        amount = Decimal(amount)
    except Exception as e:
        logger.error(f"Invalid amount '{amount}' for deal {deal_id}: {e}")
        return

    if amount > 0 and component_type in VALID_COMPONENTS:
        try:
            Transaction.objects.create(
                deal_id=str(deal_id),
                transaction_type='Earned',
                incentive_component_type=component_type,
                amount=amount,
                freeze=False,
                is_latest=True,
                eligibility_status='Pending',
                created_by=user,
                updated_by=user
            )
            logger.info(f"Transaction created: Deal={deal_id}, Type={component_type}, Amount={amount}")
        except Exception as e:
            logger.error(f"Error creating transaction for deal {deal_id}: {e}")
    else:
        logger.debug(f"Skipped transaction for deal {deal_id}: Invalid type or zero amount [{component_type}, {amount}]")

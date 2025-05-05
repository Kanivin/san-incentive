from ..models import Transaction, PayoutTransaction
from django.db import transaction


def process_deal_incentives(deal_info, bifurcation_slabs):
    deal_id = deal_info["deal_id"]
    roles = deal_info["roles"]

    # Fetch the latest incentive transactions for this deal
    incentive_transactions = Transaction.objects.filter(
        deal_id=deal_id,
        is_latest=True
    )

    with transaction.atomic():
        for incentive in incentive_transactions:
            component_type = incentive.incentive_component_type
            total_amount = incentive.amount

            # Get bifurcation config for this component (e.g., {'deal_owner': 40, 'deal_source': 30, ...})
            bifurcation = bifurcation_slabs.get(component_type, {})

            for role, percentage in bifurcation.items():
                user_id = roles.get(role)
                if not user_id or percentage <= 0:
                    continue  # Skip empty or 0%

                payout_amount = round(total_amount * (percentage / 100), 2)

                # Create a payout record
                PayoutTransaction.objects.create(
                    deal_id=deal_id,
                    incentive_transaction=incentive,
                    user_id=user_id,
                    incentive_person_type=role,
                    payout_amount=payout_amount,
                    payout_status='Pending',
                    payment_method='Bank Transfer',
                    created_by=incentive.created_by,
                    updated_by=incentive.updated_by
                )

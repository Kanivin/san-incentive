import logging
from decimal import Decimal
from django.db import transaction
from ..models import Transaction, PayoutTransaction

logger = logging.getLogger(__name__)

def process_deal_incentives(deal_info, bifurcation_slabs):
    deal_id = deal_info["deal_id"]
    roles = deal_info["roles"]

    try:
        incentive_transactions = Transaction.objects.filter(
            deal_id=deal_id,
            is_latest=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch incentive transactions for deal {deal_id}: {str(e)}")
        return

    with transaction.atomic():
        for incentive in incentive_transactions:
            component_type = incentive.incentive_component_type
            total_amount = incentive.amount or Decimal("0.00")

            bifurcation = bifurcation_slabs.get(component_type)

            if not bifurcation or not isinstance(bifurcation, dict):
                logger.warning(
                    f"Skipping component '{component_type}' for deal {deal_id} due to missing or invalid bifurcation config"
                )
                continue

            for role, percentage in bifurcation.items():
                user_id = roles.get(role)

                if not user_id:
                    logger.debug(f"No user assigned to role '{role}' for deal {deal_id}, skipping.")
                    continue

                try:
                    percentage = Decimal(str(percentage))
                    if percentage <= 0:
                        continue
                except Exception as e:
                    logger.warning(f"Invalid percentage '{percentage}' for role '{role}' in deal {deal_id}: {str(e)}")
                    continue

                payout_amount = round(total_amount * (percentage / Decimal("100.0")), 2)

                try:
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
                    logger.info(
                        f"PayoutTransaction created: Deal={deal_id}, Role={role}, Amount={payout_amount}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to create payout transaction for deal {deal_id}, role {role}: {str(e)}"
                    )

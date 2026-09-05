from dataclasses import dataclass
from typing import Optional

@dataclass
class CanonicalField:
    name: str
    required: bool
    data_type: str
    description: Optional[str] = None

CANONICAL_SCHEMA = {
    "transaction_id": CanonicalField(
        name="transaction_id",
        required=True,
        data_type="string",
        description="Unique transaction reference"
    ),
    "amount": CanonicalField(
        name="amount",
        required=True,
        data_type="float",
        description="Transaction amount"
    ),
    "status": CanonicalField(
        name="status",
        required=True,
        data_type="string",
        description="Transaction status"
    ),
    "date": CanonicalField(
        name="date",
        required=False,
        data_type="datetime",
        description="Transaction date"
    ),
    "currency": CanonicalField(
        name="currency",
        required=False,
        data_type="string",
        description="Transaction currency"
    ),
    "customer": CanonicalField(
        name="customer",
        required=False,
        data_type="string",
        description="Customer name"
    )
}
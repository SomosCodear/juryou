from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from . import backend
from .company import Company
from .customer import Customer

C_INVOICE_TYPE = 11
INVOICE_CONCEPT = 3


class Item:
    def __init__(self, name: str, amount: int, price: Decimal):
        self.name = name
        self.amount = amount
        self.price = price

    @property
    def total(self):
        return self.price * self.amount


class Receipt:
    def __init__(
        self,
        company: Company,
        customer: Customer,
        point_of_sale: int,
        backend: 'backend.AFIPBackend',
        date: Optional[datetime] = None,
        type: int = C_INVOICE_TYPE,
        concept: int = INVOICE_CONCEPT,
    ):
        self.company = company
        self.customer = customer
        self.backend = backend
        self.date = date if date is not None else datetime.now(timezone.utc)
        self.point_of_sale = point_of_sale
        self.type = type
        self.concept = concept
        self.items: [Item] = []
        self.number: int = None
        self.cae: str = None
        self.cae_expiration: datetime = None
        self.confirmation_code: str = None

    def commit(self):
        return self.backend.commit(self)

    def generate_pdf(self):
        pass

    def add_item(self, name: str, amount: int, price: Decimal):
        self.items.append(
            Item(name, amount, price)
        )

        return self

    @property
    def total(self):
        return Decimal(sum(item.total for item in self.items))

    @property
    def invoice_type_letter(self):
        if self.invoice_type == C_INVOICE_TYPE:
            return 'C'

    def _generate_verification_number(self, code):
        odd = sum(int(code[index]) for index in range(1, len(code), 2)) * 3
        even = sum(int(code[index]) for index in range(0, len(code), 2))
        total = odd + even

        return 10 - total % 10

    @property
    def code(self):
        code = '{}{:03d}{:05d}{}{}'.format(
            self.company.cuit,
            self.type,
            self.point_of_sale,
            self.cae,
            self.date.strftime(self.backend.WSFEV1_DATE_FORMAT),
        )

        verification_code = self._generate_verification_number(code)
        code += str(verification_code)

        return code

from typing import Optional


class Company:
    def __init__(
        self,
        name: str,
        address: str,
        cuit: str,
        brute_income: str,
        iva: str,
        start_of_operations: str,
        short_name: Optional[str] = None,
    ):
        self.name = name
        self.short_name = short_name if short_name is not None else name
        self.address = address
        self.cuit = cuit
        self.brute_income = brute_income
        self.iva = iva
        self.start_of_operations = start_of_operations

import factory

from juryou.receipt import Receipt, Item
from .company_factory import CompanyFactory
from .customer_factory import CustomerFactory


class ItemFactory(factory.Factory):
    name = factory.Faker('word')
    amount = factory.Faker('random_digit_not_null')
    price = factory.Faker('pydecimal')

    class Meta:
        model = Item
        inline_args = ['name', 'amount', 'price']


class ReceiptFactory(factory.Factory):
    company = factory.SubFactory(CompanyFactory)
    customer = factory.SubFactory(CustomerFactory)
    point_of_sale = factory.Faker('random_digit_not_null')

    class Meta:
        model = Receipt
        inline_args = ['company', 'customer', 'point_of_sale', 'backend']

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        if extracted:
            for item in extracted:
                self.add_item(**item)
        else:
            self.items = [ItemFactory() for i in range(5)]

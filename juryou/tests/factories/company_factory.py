import factory
from juryou.company import Company


class CompanyFactory(factory.Factory):
    name = factory.Faker('company')
    address = factory.Faker('address')
    cuit = factory.Faker('numerify', text='#############')
    brute_income = factory.Faker('word')
    iva = factory.Faker('word')
    start_of_operations = factory.Faker('date_this_year')

    class Meta:
        model = Company
        inline_args = ['name', 'address', 'cuit', 'brute_income', 'iva', 'start_of_operations']

import factory
from juryou.customer import Customer


class CustomerFactory(factory.Factory):
    identity_document = factory.Faker('numerify', text='########')
    name = factory.Faker('name')

    class Meta:
        model = Customer
        inline_args = ['identity_document', 'name']

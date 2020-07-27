import json
import juryou
import decimal
from datetime import datetime


def generate(backend: juryou.AFIPBackend, input_filename: str, output_filename: str):
    with open(input_filename, 'r') as receipt_file:
        receipt_data = json.load(receipt_file)

    company = juryou.Company(
        receipt_data['company']['name'],
        receipt_data['company']['address'],
        receipt_data['company']['cuit'],
        receipt_data['company']['brute_income'],
        receipt_data['company']['iva'],
        datetime.strptime(receipt_data['company']['start_of_operations'], '%Y-%m-%d'),
        receipt_data['company'].get('short_name'),
    )
    customer = juryou.Customer(
        receipt_data['customer']['identity_document'],
        receipt_data['customer']['name'],
    )
    receipt = juryou.Receipt(
        company,
        customer,
        receipt_data['point_of_sale'],
        backend,
    )

    for item in receipt_data['items']:
        receipt.add_item(item['name'], item['amount'], decimal.Decimal(item['price']))

    receipt.commit()

    with open(output_filename, '+wb') as output_file:
        receipt.generate_pdf(output_file)

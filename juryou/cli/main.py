import os
import json
import argparse
import decimal
import juryou

parser = argparse.ArgumentParser(description='Generate a receipt')
parser.add_argument('receipt_file',
                    help='path to the file containing json data to generate the receipt')
parser.add_argument('output_file',
                    help='path for the output file (invoice pdf)')
parser.add_argument('--certificate', required=True,
                    help='AFIP certificate to use for the receipt generation')
parser.add_argument('--private-key', required=True,
                    help='private key file path used for the recipt generation')
parser.add_argument('--cuit', required=True,
                    help='cuit of the company used for the recipt generation')
parser.add_argument('--credentials', required=True,
                    help='file containing the credentials/where to write the credentials')


def main():
    args = parser.parse_args()

    with open(args.certificate, 'r') as certificate_file, \
            open(args.private_key, 'r') as private_key_file, \
            open(args.receipt_file, 'r') as receipt_file:
        certificate = certificate_file.read()
        private_key = private_key_file.read()
        receipt_data = json.load(receipt_file)

    if os.path.exists(args.credentials):
        with open(args.credentials, 'r+') as credentials_file:
            credentials = json.load(credentials_file)
    else:
        credentials = None

    backend = juryou.AFIPBackend(certificate, private_key, args.cuit, credentials)

    company = juryou.Company(
        receipt_data['company']['name'],
        receipt_data['company']['address'],
        receipt_data['company']['cuit'],
        receipt_data['company']['brute_income'],
        receipt_data['company']['iva'],
        receipt_data['company']['start_of_operations'],
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

    with open(args.credentials) as credentials_file, \
            open(args.output_file, '+wb') as output_file:
        json.dump(backend.credentials, credentials_file)
        receipt.generate_pdf(output_file)

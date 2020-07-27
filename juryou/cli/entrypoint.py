import argparse
import os
import json
import juryou
from .generate import generate
from .print_invoice import print_invoice

parser = argparse.ArgumentParser(description='Generate/Retrieve a receipt')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--receipt-file',
                   help='path to the file containing json data to generate the receipt')
group.add_argument('--receipt-identifier',
                   help='identifier of a receipt to fetch')
parser.add_argument('--output-file',
                    help='path for the output file (invoice pdf)')
parser.add_argument('--certificate', required=True,
                    help='AFIP certificate to use for the receipt generation')
parser.add_argument('--private-key', required=True,
                    help='private key file path used for the recipt generation')
parser.add_argument('--cuit', required=True,
                    help='cuit of the company used for the recipt generation')
parser.add_argument('--credentials', required=True,
                    help='file containing the credentials/where to write the credentials')
parser.add_argument('--production', action='store_true',
                    help="indicates to use the production resource url")


def main():
    args = parser.parse_args()

    with open(args.certificate, 'r') as certificate_file, \
            open(args.private_key, 'r') as private_key_file:
        certificate = certificate_file.read()
        private_key = private_key_file.read()

    if os.path.exists(args.credentials):
        with open(args.credentials, 'r+') as credentials_file:
            credentials = json.load(credentials_file)
    else:
        credentials = None

    backend = juryou.AFIPBackend(certificate, private_key, args.cuit, credentials, args.production)

    if args.receipt_file:
        if args.output_file is None:
            print('You need to provide an output file')
        else:
            generate(backend, args.receipt_file, args.output_file)
    elif args.receipt_identifier:
        print_invoice(backend, args.receipt_identifier)
    else:
        print('Provide either receipt and output file or a receipt identifier')

    with open(args.credentials, '+w') as credentials_file:
        json.dump(backend.credentials, credentials_file)

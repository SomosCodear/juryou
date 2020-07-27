import juryou


def print_invoice(backend: juryou.AFIPBackend, identifier: str):
    if identifier.endswith('last'):
        identifier = ':'.join(identifier.split(':')[:-1])
        receipt = backend.fetch_last(identifier)
    else:
        receipt = backend.fetch(identifier)

    print('Retrieved receipt:')
    print('Date:', receipt.date.strftime('%d-%m-%Y'))
    print('Customer Identity Document:', receipt.customer.identity_document)
    print('Total:', receipt.total)

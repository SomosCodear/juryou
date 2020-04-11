CUIT_LENGTH = 11
INVOICE_CUIT_DOCUMENT_TYPE = 80
INVOICE_NATIONAL_DOCUMENT_TYPE = 96


class Customer:
    def __init__(self, identity_document, name):
        self.identity_document = identity_document
        self.name = name

    @property
    def identity_document_type(self):
        return (
            INVOICE_NATIONAL_DOCUMENT_TYPE
            if len(self.identity_document) == CUIT_LENGTH
            else INVOICE_CUIT_DOCUMENT_TYPE
        )

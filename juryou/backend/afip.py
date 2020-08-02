from typing import Optional
from datetime import datetime, timezone
from py3afipws import wsaa, wsfev1
from juryou import receipt, company, customer, utils
from .base import BaseBackend

WSAA_PRODUCTION_URL = 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
WSFEV1_PRODUCTION_URL = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'


class MissingCustomerDataError(Exception):
    pass


class EmptyInvoiceError(Exception):
    pass


class WrongIdentifier(Exception):
    pass


class AFIPBackend(BaseBackend):
    TRA_TTL = 36000
    TOKEN_CACHE_KEY = 'TOKEN'
    SIGN_CACHE_KEY = 'SIGN'
    EXPIRATION_CACHE_KEY = 'EXPIRATION'
    EXPIRATION_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
    WSFEV1_DATE_FORMAT = '%Y%m%d'

    def __init__(
        self,
        certificate: str,
        private_key: str,
        cuit: str,
        credentials: Optional[dict] = None,
        production: bool = False,
        cache: Optional[str] = None,
    ):
        self.certificate = certificate
        self.private_key = private_key
        self.cuit = cuit
        self.credentials = {**credentials} if credentials is not None else {}
        self.production = production
        self.cache = cache

    def validate_receipt(self, receipt: 'receipt.Receipt') -> None:
        if not receipt.customer.name or not receipt.customer.identity_document:
            raise MissingCustomerDataError()

        if not receipt.total:
            raise EmptyInvoiceError()

    def commit(self, receipt: 'receipt.Receipt') -> 'receipt.Receipt':
        self.validate_receipt(receipt)
        client = self._get_client()
        invoice_number = int(client.CompUltimoAutorizado(
            receipt.type,
            receipt.point_of_sale,
        )) + 1

        formatted_invoice_date = receipt.date.strftime(self.WSFEV1_DATE_FORMAT)
        formatted_total = str(utils.quantize_decimal(receipt.total))

        client.CrearFactura(
            concepto=receipt.concept,
            tipo_doc=receipt.customer.identity_document_type,
            nro_doc=receipt.customer.identity_document,
            tipo_cbte=receipt.type,
            punto_vta=receipt.point_of_sale,
            cbt_desde=invoice_number,
            cbt_hasta=invoice_number,
            imp_total=formatted_total,
            imp_neto=formatted_total,
            fecha_cbte=formatted_invoice_date,
        )
        client.CAESolicitar()

        receipt.number = invoice_number
        receipt.cae = client.CAE
        receipt.cae_expiration = datetime.strptime(
            client.Vencimiento,
            self.WSFEV1_DATE_FORMAT,
        )

        return receipt

    def _parse_identifier(self, identifier: str):
        try:
            (point_of_sale, invoice_type, invoice_number) = identifier.split(':')

            return int(point_of_sale), int(invoice_type), int(invoice_number)
        except ValueError:
            raise WrongIdentifier(identifier)

    def fetch(self, identifier: str):
        (point_of_sale, invoice_type, invoice_number) = self._parse_identifier(identifier)

        client = self._get_client()
        client.CompConsultar(invoice_type, point_of_sale, invoice_number)

        receipt_company = company.DummyCompany()
        receipt_customer = customer.Customer(client.factura['nro_doc'], '')
        fetched_receipt = receipt.Receipt(
            receipt_company,
            receipt_customer,
            point_of_sale,
            self,
            datetime.strptime(client.factura['fecha_cbte'], self.WSFEV1_DATE_FORMAT),
            client.factura['tipo_cbte'],
            client.factura['concepto'],
        )
        fetched_receipt.add_item('Item', 1, client.factura['imp_total'])
        fetched_receipt.number = invoice_number
        fetched_receipt.cae = client.factura['cae']
        fetched_receipt.cae_expiration = datetime.strptime(
            client.factura['fch_venc_cae'],
            self.WSFEV1_DATE_FORMAT,
        )

        return fetched_receipt

    def fetch_last(self, identifier: str, count: int = 1):
        (point_of_sale, invoice_type, _) = self._parse_identifier(identifier + ':0')
        client = self._get_client()
        last_invoice_number = int(client.CompUltimoAutorizado(invoice_type, point_of_sale))
        receipts = []

        for i in range(0, count):
            invoice_id = f'{identifier}:{last_invoice_number - i}'
            receipt = self.fetch(invoice_id)

            receipts.append(receipt)

        return receipt

    def _authenticate(self):
        if self.EXPIRATION_CACHE_KEY in self.credentials and (
            datetime.strptime(
                self.credentials[self.EXPIRATION_CACHE_KEY],
                self.EXPIRATION_DATE_FORMAT,
            ) < datetime.now(timezone.utc)
        ):
            self.credentials = {}

        if self.TOKEN_CACHE_KEY not in self.credentials \
                or self.SIGN_CACHE_KEY not in self.credentials:
            wsdl = WSAA_PRODUCTION_URL if self.production else None
            wsaa_client = wsaa.WSAA()

            tra = wsaa_client.CreateTRA('wsfe', ttl=self.TRA_TTL)
            cms = wsaa_client.SignTRA(tra, self.certificate, self.private_key)

            wsaa_client.Conectar(wsdl=wsdl, cache=self.cache)
            wsaa_client.LoginCMS(cms)
            self.credentials[self.TOKEN_CACHE_KEY] = wsaa_client.Token
            self.credentials[self.SIGN_CACHE_KEY] = wsaa_client.Sign
            self.credentials[self.EXPIRATION_CACHE_KEY] = wsaa_client.ObtenerTagXml(
                'expirationTime',
            )

        return self.credentials[self.TOKEN_CACHE_KEY], self.credentials[self.SIGN_CACHE_KEY]

    def _get_client(self):
        wsdl = WSFEV1_PRODUCTION_URL if self.production else None
        token, sign = self._authenticate()

        wsfev1_client = wsfev1.WSFEv1()
        wsfev1_client.Token = token.encode('utf-8')
        wsfev1_client.Sign = sign.encode('utf-8')
        wsfev1_client.Cuit = self.cuit
        wsfev1_client.Conectar(wsdl=wsdl, cache=self.cache)

        return wsfev1_client

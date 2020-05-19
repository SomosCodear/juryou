from typing import Optional
from datetime import datetime, timezone
from py3afipws import wsaa, wsfev1
from juryou import receipt, utils
from .base import BaseBackend

WSAA_PRODUCTION_URL = 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
WSFEV1_PRODUCTION_URL = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'


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

    def commit(self, receipt: 'receipt.Receipt') -> 'receipt.Receipt':
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

    def _authenticate(self):
        wsdl = WSAA_PRODUCTION_URL if self.production else None
        wsaa_client = wsaa.WSAA()

        if self.EXPIRATION_CACHE_KEY in self.credentials and (
            datetime.strptime(
                self.credentials[self.EXPIRATION_CACHE_KEY],
                self.EXPIRATION_DATE_FORMAT
            ) < datetime.now(timezone.utc)
        ):
            self.credentials = {}

        if self.TOKEN_CACHE_KEY not in self.credentials \
                or self.SIGN_CACHE_KEY not in self.credentials:
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

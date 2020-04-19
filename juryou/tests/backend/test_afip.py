import faker
import freezegun
from unittest import mock, TestCase
from datetime import datetime, timedelta, timezone

from juryou import utils
from juryou.tests import factories
from juryou.backend import afip

fake = faker.Faker()


@mock.patch('juryou.backend.afip.wsfev1')
@mock.patch('juryou.backend.afip.wsaa')
class AfipGetClientTestCase(TestCase):
    def setUp(self):
        certificate = fake.paragraph()
        private_key = fake.paragraph()
        cuit = fake.numerify(text='###########')
        self.afip = afip.AFIPBackend(certificate, private_key, cuit)

    def test_should_store_token_and_sign_internally(self, wsaa, wsfev1):
        # arrange
        token = fake.lexify(text='?????????')
        sign = fake.lexify(text='?????????')
        expiration = fake.date_time_between(
            start_date='now',
        ).strftime(self.afip.EXPIRATION_DATE_FORMAT)
        wsaa.WSAA.return_value.Token = token
        wsaa.WSAA.return_value.Sign = sign
        wsaa.WSAA.return_value.ObtenerTagXml.return_value = expiration

        # act
        self.afip._get_client()

        # assert
        self.assertEqual(self.afip.credentials[self.afip.TOKEN_CACHE_KEY], token)
        self.assertEqual(self.afip.credentials[self.afip.SIGN_CACHE_KEY], sign)
        self.assertEqual(self.afip.credentials[self.afip.EXPIRATION_CACHE_KEY], expiration)

    def test_should_use_stored_token_and_sign_if_saved(self, wsaa, wsfev1):
        # arrange
        token = fake.lexify(text='?????????')
        sign = fake.lexify(text='?????????')
        expiration = fake.date_time_between(
            start_date=datetime.now() + timedelta(hours=1),
            end_date=datetime.now() + timedelta(days=1),
            tzinfo=timezone.utc,
        ).strftime(self.afip.EXPIRATION_DATE_FORMAT)
        self.afip.credentials = {
            self.afip.TOKEN_CACHE_KEY: token,
            self.afip.SIGN_CACHE_KEY: sign,
            self.afip.EXPIRATION_CACHE_KEY: expiration,
        }

        # act
        client = self.afip._get_client()

        # assert
        self.assertEqual(client.Token, token.encode('utf-8'))
        self.assertEqual(client.Sign, sign.encode('utf-8'))

    def test_should_not_use_stored_token_and_sign_if_expired(self, wsaa, wsfev1):
        # arrange
        old_token = fake.lexify(text='?????????')
        old_sign = fake.lexify(text='?????????')
        old_expiration = fake.date_time_between(
            end_date='now',
            tzinfo=timezone.utc,
        ).strftime(self.afip.EXPIRATION_DATE_FORMAT)
        self.afip.credentials = {
            self.afip.TOKEN_CACHE_KEY: old_token,
            self.afip.SIGN_CACHE_KEY: old_sign,
            self.afip.EXPIRATION_CACHE_KEY: old_expiration,
        }

        new_token = fake.lexify(text='?????????')
        new_sign = fake.lexify(text='?????????')
        new_expiration = fake.date_time_between(
            start_date='now',
        ).strftime(self.afip.EXPIRATION_DATE_FORMAT)
        wsaa.WSAA.return_value.Token = new_token
        wsaa.WSAA.return_value.Sign = new_sign
        wsaa.WSAA.return_value.ObtenerTagXml.return_value = new_expiration

        # act
        client = self.afip._get_client()

        # assert
        self.assertEqual(client.Token, new_token.encode('utf-8'))
        self.assertEqual(client.Sign, new_sign.encode('utf-8'))
        self.assertEqual(self.afip.credentials[self.afip.TOKEN_CACHE_KEY], new_token)
        self.assertEqual(self.afip.credentials[self.afip.SIGN_CACHE_KEY], new_sign)
        self.assertEqual(self.afip.credentials[self.afip.EXPIRATION_CACHE_KEY], new_expiration)


class AfipGenerateInvoiceTestCase(TestCase):
    def setUp(self):
        certificate = fake.paragraph()
        private_key = fake.paragraph()
        cuit = fake.numerify(text='###########')
        self.afip = afip.AFIPBackend(certificate, private_key, cuit)
        self.afip._get_client = mock.MagicMock()
        self.receipt = factories.ReceiptFactory(backend=self.afip)

    @freezegun.freeze_time(datetime.now())
    def test_should_create_cae(self):
        # arrange
        invoice_number = 5
        invoice_total = str(utils.quantize_decimal(self.receipt.total))
        invoice_date = self.receipt.date.strftime('%Y%m%d')
        cae_expiration = datetime(2020, 3, 9)

        afip_client = self.afip._get_client.return_value
        afip_client.CompUltimoAutorizado.return_value = invoice_number - 1
        afip_client.CAE = 1234
        afip_client.Vencimiento = cae_expiration.strftime(self.afip.WSFEV1_DATE_FORMAT)

        expected_invoice = {
            'concepto': self.receipt.concept,
            'tipo_doc': self.receipt.customer.identity_document_type,
            'nro_doc': self.receipt.customer.identity_document,
            'tipo_cbte': self.receipt.type,
            'punto_vta': self.receipt.point_of_sale,
            'cbt_desde': invoice_number,
            'cbt_hasta': invoice_number,
            'imp_total': invoice_total,
            'imp_neto': invoice_total,
            'fecha_cbte': invoice_date,
        }

        # act
        receipt = self.afip.commit(self.receipt)

        # assert
        afip_client.CrearFactura.assert_called_once_with(**expected_invoice)
        afip_client.CAESolicitar.assert_called_once()
        self.assertEqual(receipt.number, invoice_number)
        self.assertEqual(receipt.cae, afip_client.CAE)
        self.assertEqual(receipt.cae_expiration, cae_expiration)

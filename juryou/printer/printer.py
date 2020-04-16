import io
import weasyprint
from typing import IO
from jinja2 import Environment, PackageLoader, select_autoescape

from juryou import receipt


class Printer:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('juryou.printer', 'templates'),
            autoescape=select_autoescape(['html']),
        )

    def print(self, receipt: 'receipt.Receipt', buffer: IO = None) -> IO:
        if buffer is None:
            buffer = io.BytesIO()

        invoice_template = self.env.get_template('invoice.html')
        invoice_html = invoice_template.render(receipt=receipt)
        invoice_pdf_font_config = weasyprint.fonts.FontConfiguration()
        invoice_pdf_writer = weasyprint.HTML(string=invoice_html)
        invoice_pdf_writer.write_pdf(buffer, font_config=invoice_pdf_font_config)

        return buffer

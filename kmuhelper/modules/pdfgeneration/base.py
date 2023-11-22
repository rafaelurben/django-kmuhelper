"""Base class for PDFCreators"""

from io import BytesIO

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

from django.http import FileResponse
from django.utils import translation

_ = translation.gettext


class PDFGenerator:
    def __init__(self, *args, **kwargs):
        self.elements = []

    def _build_pdf(self):
        self.__buffer = BytesIO()
        self.__doc = SimpleDocTemplate(
            self.__buffer,
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
            pagesize=A4,
            creator="django-kmuhelper by rafaelurben",
            author="Rafael Urben (rafaelurben.ch)",
        )

        self.__doc.build(self.elements)
        self.__buffer.seek(0)

    def get_pdf(self):
        if not hasattr(self, "__buffer"):
            self._build_pdf()
        return self.__buffer

    def get_response(self, as_attachment=False, filename="document.pdf"):
        return FileResponse(
            self.get_pdf(), as_attachment=as_attachment, filename=filename
        )

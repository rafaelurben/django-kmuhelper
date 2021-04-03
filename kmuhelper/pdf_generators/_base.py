from io import BytesIO

from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, BaseDocTemplate, SimpleDocTemplate, Frame, PageTemplate, TopPadder, Flowable
from reportlab.lib.units import mm, cm
from reportlab.lib.pagesizes import A4

from django.http import FileResponse
from django.utils import translation
_ = translation.gettext

class PDFGenerator():
    def __init__(self, *args, **kwargs):
        self.language = self.get_language(*args, **kwargs)

        self.__buffer = BytesIO()
        self.__doc = SimpleDocTemplate(self.__buffer, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)

        cur_language = translation.get_language()
        translation.activate(self.language)

        self.__elements = self.get_elements(*args, **kwargs)
        self.__doc.build(self.__elements)
        self.__buffer.seek(0)

        translation.activate(cur_language)

    def get_elements(self, *args, **kwargs):
        raise NotImplementedError()

    def get_language(self, *args, **kwargs):
        print(f"[KMUHelper] - {self.__class__.__name__} - get_language hasn't been implemented, using default")
        return translation.get_language()

    def get_pdf(self):
        return self.__buffer

    def get_response(self, as_attachment=False, filename="document.pdf"):
        return FileResponse(self.__buffer, as_attachment=as_attachment, filename=filename)

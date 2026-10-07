"""Compare PyMuPDF et Docling sur une page qui contient un tableau."""

import pymupdf
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

PDF = "data/raw/journalisation.pdf"
PAGE = 29

print("=" * 30, "PyMuPDF", "=" * 30)
doc = pymupdf.open(PDF)
print(doc[PAGE - 1].get_text())

print("=" * 30, "Docling", "=" * 30)
options = PdfPipelineOptions(do_ocr=False)
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
)
result = converter.convert(PDF, page_range=(PAGE, PAGE))
print(result.document.export_to_markdown())
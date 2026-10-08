"""Conversion d'un PDF en liste d'éléments avec Docling."""

from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DoclingDocument, TableItem

from ragfr.ingestion.cleaning import clean_text, is_noise
from ragfr.ingestion.models import Element, ElementKind
from ragfr.ingestion.sections import assign_sections

# Étiquettes Docling -> nos types. Celles qui manquent sont ignorées :
# images, sommaire (document_index), en-têtes et pieds de page.
LABEL_TO_KIND: dict[str, ElementKind] = {
    "title": "heading",
    "section_header": "heading",
    "text": "paragraph",
    "paragraph": "paragraph",
    "list_item": "list_item",
    "table": "table",
    "caption": "caption",
    "footnote": "footnote",
    "code": "code",
}


def make_converter() -> DocumentConverter:
    """Crée le convertisseur. Coûteux (chargement des modèles) : à faire une seule fois."""
    options = PdfPipelineOptions(do_ocr=False)  # PDF natifs : l'OCR est inutile et très lent
    options.table_structure_options.mode = TableFormerMode.ACCURATE
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})


def convert(converter: DocumentConverter, pdf_path: Path) -> DoclingDocument:
    return converter.convert(pdf_path).document


def _is_table_caption(item) -> bool:
    # La légende d'un tableau est déjà incluse dans le texte du tableau.
    return item.parent is not None and item.parent.cref.startswith("#/tables/")


def to_elements(doc: DoclingDocument) -> list[Element]:
    elements = []
    for item, _level in doc.iterate_items():
        kind = LABEL_TO_KIND.get(str(item.label))
        if kind is None or not item.prov:
            continue
        if kind == "caption" and _is_table_caption(item):
            continue

        if isinstance(item, TableItem):
            caption = item.caption_text(doc)
            table_md = item.export_to_markdown(doc=doc)
            raw = f"{caption}\n\n{table_md}" if caption else table_md
        else:
            raw = item.text

        text = clean_text(raw, kind)
        if is_noise(text):
            continue
        pages = [p.page_no for p in item.prov]
        elements.append(Element(kind=kind, text=text, page=min(pages), page_end=max(pages)))
    return assign_sections(elements)

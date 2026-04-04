import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from pathlib import Path
import shutil
from rich.progress import Progress

def extract_text_pdfplumber(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    return "\n\n".join(pages).strip()

def extract_text_ocr(pdf_path: str, lang: str = "eng+guj") -> str:
    """Fallback: rasterize pages and run Tesseract OCR.
    lang='eng+guj' handle the bilinngual Gujarati+English docs.
    """
    if shutil.which("tesseract") is None:
        raise RuntimeError("Tesseract OCR is not installed. Please install it to use OCR features.")
        

    images = convert_from_path(pdf_path, dpi=200)
    pages = []

    with Progress() as progress:
    
        task = progress.add_task(f"[cyan]Running OCR on {pdf_path}...", total=len(images))
    
        for image in images:
            text = pytesseract.image_to_string(image, lang=lang)
            pages.append(text)

            progress.advance(task)
    
    return "\n\n".join(pages).strip()

def extract_text(pdf_path:str)->tuple[str,str]:
    """
    Returns (text, method_used).
    Tries pdfplumber first; falls back to OCR if text is too short.
    Threshold: if extracted text < 100 chars, assume scanned doc.
    """
    text = extract_text_pdfplumber(pdf_path)
    if len(text.strip()) > 100:
        return text, "pdfplumber"

    #fallback to OCR
    text = extract_text_ocr(pdf_path)
    return text, "ocr"

def detect_doc_type(text: str)->list[str]:
    """
    Heuristic pre-classifier to hint the agent.
    Saves LLM tokens by narrowing the search space.
    """
    text_lower = text.lower()
    types = []

    if any(k in text_lower for k in ["e-challan", "echallan", "challan", 
                                      "inspector general of registration",
                                      "stamp duty", "registration fee"]):
        types.append("echallan")

    if any(k in text_lower for k in ["lease deed", "lease of immovable", 
                                      "lessee", "lessor", "iora"]):
        types.append("lease_deed")
    
    if any(k in text_lower for k in ["na order", "iora/", "non-agricultural",
                                      "બિનખેતી", "prant adhikari"]):
        types.append("na_order")
    
    return types if types else ["unknown"]



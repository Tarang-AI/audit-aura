import io
from pypdf import PdfReader
from pathlib import Path

pdf_path = Path("backend/data/pdfs/SOC2_2026.pdf")
if not pdf_path.exists():
    print(f"File not found: {pdf_path}")
else:
    with open(pdf_path, "rb") as f:
        content = f.read()
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n".join(text_parts)
        print(f"Extracted {len(full_text)} characters")
        print("First 200 chars:")
        print(full_text[:200])

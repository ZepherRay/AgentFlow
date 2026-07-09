from pathlib import Path


def parse_file(file_path: str) -> str:
    """解析文件内容，支持 PDF/Word/Excel/TXT"""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt":
        return path.read_text(encoding="utf-8")

    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise ImportError("PyPDF2 not installed")

    if ext in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("python-docx not installed")

    if ext in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(path))
            texts = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    texts.append("\t".join(str(c) if c is not None else "" for c in row))
            return "\n".join(texts)
        except ImportError:
            raise ImportError("openpyxl not installed")

    raise ValueError(f"Unsupported file type: {ext}")
from pathlib import Path
from app.utils.document_loaders import load_document, DocumentLoaderFactory


def parse_file(file_path: str, loader_type: str | None = None) -> str:
    return load_document(file_path, loader_type)
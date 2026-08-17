from pathlib import Path
from typing import Optional, List


class BaseLoader:
    def load(self, file_path: str) -> str:
        raise NotImplementedError


class PyMuPDFLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            import fitz
            doc = fitz.open(file_path)
            texts = []
            for page in doc:
                text = page.get_text()
                if text:
                    texts.append(text)
            return "\n\n".join(texts)
        except ImportError:
            raise ImportError("PyMuPDF (fitz) not installed")
        except Exception as e:
            raise RuntimeError(f"PyMuPDF read failed: {e}")


class PyPDF2Loader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            texts = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(texts)
        except ImportError:
            raise ImportError("PyPDF2 not installed")


class UnstructuredPDFLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from unstructured.partition.pdf import partition_pdf
            try:
                elements = partition_pdf(filename=file_path)
                return "\n\n".join(str(e) for e in elements)
            except Exception:
                from pdfminer.high_level import extract_text
                return extract_text(file_path)
        except ImportError:
            try:
                from pdfminer.high_level import extract_text
                return extract_text(file_path)
            except ImportError:
                raise ImportError("unstructured[pdf] or pdfminer.six not installed")


class DocxLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            raise ImportError("python-docx not installed")


class PandasCSVLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            lines = []
            lines.append("\t".join(df.columns))
            for _, row in df.iterrows():
                lines.append("\t".join(str(v) for v in row.values))
            return "\n".join(lines)
        except ImportError:
            raise ImportError("pandas not installed")


class MarkdownLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from markdown_it import MarkdownIt
            md = MarkdownIt()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = md.parse(content)
            texts = []
            for token in tokens:
                if token.type in ("inline", "text"):
                    texts.append(token.content)
            return "\n\n".join(texts)
        except ImportError:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()


class HTMLLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from markdown_it import MarkdownIt
            from markdown_it.extensions.html_block import makeExtension as HtmlBlock
            from markdown_it.extensions.html_inline import makeExtension as HtmlInline
            md = MarkdownIt().use(HtmlBlock).use(HtmlInline)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = md.parse(content)
            texts = []
            for token in tokens:
                if token.type in ("inline", "text"):
                    texts.append(token.content)
            return "\n\n".join(texts)
        except ImportError:
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.texts = []

                def handle_data(self, data):
                    if data.strip():
                        self.texts.append(data.strip())

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            parser = TextExtractor()
            parser.feed(content)
            return "\n\n".join(parser.texts)


class IPYNBLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        texts = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "markdown":
                source = "".join(cell.get("source", []))
                texts.append(source)
            elif cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                outputs = cell.get("outputs", [])
                output_texts = []
                for out in outputs:
                    if "text" in out:
                        output_texts.append("".join(out["text"]))
                    elif "data" in out and "text/plain" in out["data"]:
                        output_texts.append("".join(out["data"]["text/plain"]))
                if source.strip():
                    texts.append(f"代码:\n{source}")
                if output_texts:
                    output_block = "\n".join(output_texts)
                    texts.append(f"输出:\n{output_block}")
        return "\n\n".join(texts)


class TXTSimpleLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")


class PyMuPDF4LLMLoader(BaseLoader):
    """Preserves table structure and images, outputs markdown."""
    def load(self, file_path: str) -> str:
        try:
            import pymupdf4llm
            md_text = pymupdf4llm.to_markdown(file_path)
            return md_text
        except ImportError:
            raise ImportError("pymupdf4llm not installed (pip install pymupdf4llm)")
        except Exception as e:
            raise RuntimeError(f"pymupdf4llm failed: {e}")


LOADER_MAP = {
    ".pdf": [("pymupdf", PyMuPDFLoader), ("pypdf2", PyPDF2Loader), ("unstructured", UnstructuredPDFLoader), ("pymupdf4llm", PyMuPDF4LLMLoader)],
    ".docx": [("docx", DocxLoader)],
    ".doc": [("docx", DocxLoader)],
    ".csv": [("pandas", PandasCSVLoader)],
    ".md": [("markdown", MarkdownLoader)],
    ".markdown": [("markdown", MarkdownLoader)],
    ".html": [("html", HTMLLoader)],
    ".htm": [("html", HTMLLoader)],
    ".ipynb": [("ipynb", IPYNBLoader)],
    ".txt": [("simple", TXTSimpleLoader)],
    ".log": [("simple", TXTSimpleLoader)],
}


class DocumentLoaderFactory:
    @staticmethod
    def get_loader(file_path: str, loader_type: Optional[str] = None) -> BaseLoader:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in LOADER_MAP:
            raise ValueError(f"Unsupported file type: {ext}")

        loaders = LOADER_MAP[ext]

        if loader_type:
            for name, cls in loaders:
                if name == loader_type:
                    return cls()

        for name, cls in loaders:
            try:
                return cls()
            except ImportError:
                continue

        raise ImportError(f"No available loader for {ext}. Install required packages.")

    @staticmethod
    def get_supported_loaders(file_path: str) -> List[str]:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in LOADER_MAP:
            return []
        return [name for name, _ in LOADER_MAP[ext]]


def load_document(file_path: str, loader_type: Optional[str] = None) -> str:
    loader = DocumentLoaderFactory.get_loader(file_path, loader_type)
    return loader.load(file_path)
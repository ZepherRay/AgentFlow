from pathlib import Path
from app.utils.file_parser import parse_file


class DocumentService:
    @staticmethod
    async def parse_document(file_path: str) -> str:
        return parse_file(file_path)

    @staticmethod
    def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - chunk_overlap
            if start >= text_len:
                break
            if start < 0:
                start = 0
        return chunks
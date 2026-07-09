from app.utils.text_splitter import split_text


class ChunkService:
    @staticmethod
    async def split(content: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        return split_text(content, chunk_size, overlap)
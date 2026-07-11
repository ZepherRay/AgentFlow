from app.utils.chinese_splitter import get_splitter


class ChunkService:
    @staticmethod
    async def split(
        content: str,
        chunk_size: int = 500,
        overlap: int = 50,
        splitter_type: str = "sentence",
        **kwargs
    ) -> list[str]:
        splitter = get_splitter(
            splitter_type,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            **kwargs
        )
        return splitter.split_text(content)
def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按字符切分文本，支持重叠"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def split_by_paragraph(text: str) -> list[str]:
    """按段落切分"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def split_by_sentence(text: str) -> list[str]:
    """按句子切分"""
    import re
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    return [s.strip() for s in sentences if s.strip()]
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks using RecursiveCharacterTextSplitter.
    Returns a list of chunk strings.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],  # order of preference for splitting
    )
    # split_text returns list[str]
    chunks = splitter.split_text(text)
    return chunks
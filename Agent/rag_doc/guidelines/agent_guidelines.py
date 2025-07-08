from pathlib import Path
import os
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter, MarkdownTextSplitter


def get_guidelines_documents(chunk_size: int = 500, chunk_overlap: int = 100):
    """
    건강기능식품 가이드라인 문서를 읽어들여 문서를 분할하고, 분할된 문서를 반환합니다.

    Args:
        chunk_size (int): 분할된 문서의 최대 길이.
        chunk_overlap (int): 분할된 문서 간의 겹치는 길이.

    Returns:
        list[Document]: 분할된 문서 리스트.
    """
    guidelines_dir = Path(__file__).parent / "disease"
    documents = []
    # markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "Header 2")])
    markdown_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    for file in guidelines_dir.glob("*.md"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            # docs = markdown_splitter.split_text(text)
            texts = markdown_splitter.split_text(text)
            for i, text in enumerate(texts):
                documents.append(Document(page_content=text, metadata={"source": file.name, "chunk_id": i}))

            # for header in headers:
            #     documents.append(Document(page_content=header.text, metadata={"source": file.name, "header": header.level}))
    return documents


if __name__ == "__main__":
    documents = get_guidelines_documents()
    for doc in documents[:20]:
        print(doc.page_content)
        print(doc.metadata)
        print("-" * 100)

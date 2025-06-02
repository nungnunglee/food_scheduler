from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from tqdm.auto import tqdm # tqdm 임포트
import fitz
import os


def get_section_to_idx(doc, page_num):
    toc = doc.get_toc()
    if page_num > doc.page_count:
        return "N/A"
    
    for i, (level, title, start_page_num) in enumerate(toc):
        if start_page_num <= page_num:
            if toc[-1][2] <= page_num:
                return toc[-1][1]
            elif page_num < toc[i+1][2]:
                return title
            continue
        else:
            return "cover page"
    return "N/A"



def get_contents_from_pdf(file_name, doc, i: int, section: str, before_text = "", text_splitter = None) -> list[Document]:
    contents_docs = []
    page = doc.load_page(i)
    text = before_text + page.get_text()
    tables = page.find_tables()
    links = page.get_links()

    if text_splitter is None:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    text = ".\n".join(text.replace("\n", "").split("."))
    texts = text_splitter.split_text(text)

    for text in texts:
        contents_docs.append(Document(
            page_content=text,
            metadata={
                "source": file_name,
                "page": i + 1,
                "type": "text",
                "section": section
            }
        ))

    for table_idx, table in enumerate(tables):
        contents_docs.append(Document(
            page_content=table.to_pandas().to_markdown(),
            metadata={
                "source": file_name,
                "page": i + 1,
                "type": "table",
                "table_index_on_page": table_idx,
                "section": section
            }
        ))


    for link_idx, link in enumerate(links):
        if link['kind'] == fitz.LINK_URI:
            link_url = link['uri']
            contents_docs.append(
                Document(
                    page_content=f"페이지 {i + 1}에 외부 웹사이트 '{link_url}'로 연결되는 링크가 있습니다.",
                    metadata={
                        "source": file_name,
                        "page": i + 1,
                        "type": "hyperlink",
                        "link_url": link_url,
                        "link_index_on_page": link_idx,
                        "section": section
                    }
                )
            )

    return contents_docs


def get_docs_from_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """
    다양한 PDF 파일을 fitz로 읽어 RAG 시 필요한 정보를 추출한 뒤,
    LangChain의 Document 객체를 요소로 하는 리스트를 얻습니다.
    함수의 진행률을 tqdm으로 표시합니다.

    Args:
        pdf_path (str): PDF 파일의 경로.
        chunk_size (int): 텍스트 청크의 최대 길이.
        chunk_overlap (int): 텍스트 청크 간의 겹치는 길이.

    Returns:
        list[Document]: 추출된 정보를 담은 LangChain Document 객체 리스트.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        is_separator_regex=False
    )

    documents = []
    with fitz.open(pdf_path) as doc:
        file_name = os.path.basename(pdf_path)

        for page_num in tqdm(range(doc.page_count), desc=f"처리 중: {file_name}"):
            current_section = get_section_to_idx(doc, page_num+1)
            contents_docs = get_contents_from_pdf(file_name, doc, page_num, current_section, text_splitter=text_splitter)
            documents.extend(contents_docs)
    
    return documents


if __name__ == "__main__":
    test_pdf_path = "Agent/rag_doc/nutrition/Nutrition-Science-and-Everyday-Application-1694655583.pdf"

    print("\n--- PDF 문서에서 정보 추출 시작 ---")
    documents = get_docs_from_pdf(test_pdf_path)

    print(f"\n총 추출된 Document 개수: {len(documents)}\n")

    for i, doc in enumerate(documents[:15]):
        print(f"--- Document {i+1} ---")
        print(f"Type: {doc.metadata.get('type')}")
        print(f"Page: {doc.metadata.get('page', 'N/A')}")
        print(f"Content (first 100 chars): {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}\n")

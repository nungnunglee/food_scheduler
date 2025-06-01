from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from uuid import uuid4
from Agent.rag_doc.read_pdf import get_docs_from_pdf


client = QdrantClient(host="localhost", port=6333)


def setup_qdrant(collection_name, documents, embeddings):
    # Create a collection with dense vectors
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=embeddings.dimension, distance=Distance.COSINE),
    )

    qdrant = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        retrieval_mode=RetrievalMode.DENSE,
    )

    uuids = [str(uuid4()) for _ in range(len(documents))]
    qdrant.add_documents(documents=documents, ids=uuids)



if __name__ == "__main__":
    documents = get_docs_from_pdf("Agent/rag_doc/nutrition/nutrition.pdf")

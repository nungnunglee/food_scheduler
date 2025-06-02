
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
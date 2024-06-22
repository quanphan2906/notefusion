import numpy as np
from pinecone.grpc import PineconeGRPC as Pinecone
from transformers import pipeline
from load_env import pinecone_api_key

# Initialize the text embedding model
embedding_pipeline = pipeline(
    "feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2"
)


# Function to generate embeddings
def _generate_embeddings(texts):
    embeddings = [np.mean(embedding_pipeline(text)[0], axis=0) for text in texts]
    return embeddings


# Initialize Pinecone
pinecone = Pinecone(api_key=pinecone_api_key)


# Create or connect to an index
index_name = "text-similarity"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=384, metric="cosine")
index = pinecone.Index(index_name)


# Function to save embeddings to Pinecone
def _save_embeddings_to_pinecone(texts, embeddings):
    items = [
        {"id": str(i), "values": embedding.tolist(), "metadata": {"text": text}}
        for i, (text, embedding) in enumerate(zip(texts, embeddings))
    ]
    index.upsert(items)


def save_text_to_db(texts):
    # Generate embeddings
    embeddings = _generate_embeddings(texts)

    # Save embeddings to Pinecone
    _save_embeddings_to_pinecone(texts, embeddings)

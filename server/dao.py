import numpy as np
import uuid
from pinecone import Pinecone
from transformers import pipeline
from load_env import pinecone_api_key

# Initialize the text embedding model
embedding_pipeline = pipeline(
    "feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2"
)


# Function to generate embeddings
def _generate_embeddings(texts: list[str]):
    embeddings = [np.mean(embedding_pipeline(text)[0], axis=0) for text in texts]
    return embeddings


# Initialize Pinecone
pinecone = Pinecone(api_key=pinecone_api_key)
VECTOR_DIMENSIONS = 384
DUMMY_TOPK_TO_QUERY_WITH_METADATA = 10000


# Create or connect to an index
index_name = "text-similarity"
index = pinecone.Index(index_name)


# Function to save embeddings to Pinecone
def _save_embeddings_to_pinecone(titles, texts, embeddings):
    items = [
        {
            "id": str(uuid.uuid4()),
            "values": embedding.tolist(),
            "metadata": {"text": text, "title": title},
        }
        for (title, text, embedding) in zip(titles, texts, embeddings)
    ]
    index.upsert(items)


def save_text_to_db(titles, texts):
    # Generate embeddings
    embeddings = _generate_embeddings(texts)

    # Save embeddings to Pinecone
    _save_embeddings_to_pinecone(titles, texts, embeddings)


def query_similar_texts(text: str, top_k=5):
    embeddings = _generate_embeddings([text])
    results = index.query(queries=[embeddings], top_k=top_k)
    similar_texts = [
        {"text": match["metadata"]["text"], "title": match["metadata"]["title"]}
        for match in results["matches"]
    ]
    return similar_texts


def update_doc(old_title: str, new_title: str = None, new_blocks: list[str] = []):
    # Query the Pinecone index
    # https://community.pinecone.io/t/is-there-a-way-to-query-all-the-vectors-and-or-metadata-from-a-namespace/797/7
    results = index.query(
        vector=[0 for _ in range(VECTOR_DIMENSIONS)],
        top_k=DUMMY_TOPK_TO_QUERY_WITH_METADATA,
        include_metadata=True,
        filter={"title": old_title},
    )

    ids_to_delete = [match["id"] for match in results["matches"]]

    if len(ids_to_delete) == 0:
        return

    # only title changes, blocks don't change
    if new_title and len(new_blocks) == 0:
        items = [
            {
                "id": match["id"],
                "values": match["value"],
                "metadata": {"text": match["metadata"]["text"], "title": new_title},
            }
            for match in results["matches"]
        ]
        index.upsert(items)

    # the blocks changed, so we have to delete the old blocks and create new ones
    index.delete(ids=ids_to_delete)

    if new_title and new_blocks:
        titles = [new_title] * len(new_blocks)
        save_text_to_db(titles, new_blocks)

import numpy as np
import uuid
from pinecone import Pinecone
from transformers import pipeline
from load_env import pinecone_api_key
from typing import Union

pinecone = Pinecone(api_key=pinecone_api_key)
VECTOR_DIMENSIONS = 384
DUMMY_TOPK_TO_QUERY_WITH_METADATA = 10000
INDEX_NAME = "text-similarity-2"
index = pinecone.Index(INDEX_NAME)

# Initialize the text embedding model
_embedding_pipeline = pipeline(
    "feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2"
)


# Function to generate embeddings
def _generate_embeddings(texts: list[str]):
    embeddings = [
        np.mean(_embedding_pipeline(text)[0], axis=0).tolist() for text in texts
    ]
    print(embeddings)
    return embeddings


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
    results = index.query(vector=embeddings[0], top_k=top_k, include_metadata=True)
    print(results)
    similar_texts = [
        {"text": match["metadata"].get("text"), "title": match["metadata"].get("title")}
        for match in results["matches"]
    ]
    return similar_texts


def upsert_doc(
    old_title: str = None,
    new_title: str = None,
    new_blocks: Union[list[str], None] = [],
):

    # there's nothing to update
    if new_title is None and (new_blocks is None or len(new_blocks) == 0):
        return

    if old_title is not None:
        # Hacky way to query with metadata only
        # https://community.pinecone.io/t/is-there-a-way-to-query-all-the-vectors-and-or-metadata-from-a-namespace/797/7
        results = index.query(
            vector=[0 for _ in range(VECTOR_DIMENSIONS)],
            top_k=DUMMY_TOPK_TO_QUERY_WITH_METADATA,
            include_metadata=True,
            filter={"title": old_title},
        )

        if len(results["matches"]) == 0:
            return

        # if only the title was changed
        # we want to upsert the title of the blocks instead of
        # deleting the blocks and creating new ones
        if new_blocks is None or len(new_blocks) == 0:
            items = [
                {
                    "id": match["id"],
                    "values": match["value"],
                    "metadata": {"text": match["metadata"]["text"], "title": new_title},
                }
                for match in results["matches"]
            ]
            index.upsert(items)
            return

        # the blocks changed, so we have to delete the old blocks and create new ones
        ids_to_delete = [match["id"] for match in results["matches"]]
        index.delete(ids=ids_to_delete)

    if new_title and new_blocks:
        titles = [new_title] * len(new_blocks)
        save_text_to_db(titles, new_blocks)


def delete_doc(title: Union[str, None]):
    if title is None:
        return

    results = index.query(
        vector=[0 for _ in range(VECTOR_DIMENSIONS)],
        top_k=DUMMY_TOPK_TO_QUERY_WITH_METADATA,
        include_metadata=True,
        filter={"title": title},
    )

    ids_to_delete = [match["id"] for match in results["matches"]]
    index.delete(ids=ids_to_delete)

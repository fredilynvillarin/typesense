"""Streamlit app for testing semantic search over category definitions."""
from __future__ import annotations

import os
from typing import List

import streamlit as st
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import typesense


@st.cache_resource(show_spinner=False)
def get_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


@st.cache_resource(show_spinner=False)
def get_client(host: str, port: int, protocol: str, api_key: str) -> typesense.Client:
    return typesense.Client(
        {
            "nodes": [{"host": host, "port": port, "protocol": protocol}],
            "api_key": api_key,
            "connection_timeout_seconds": 10,
        }
    )


def format_embedding(vector: List[float]) -> str:
    return ",".join(f"{value:.8f}" for value in vector)


def main() -> None:
    st.set_page_config(page_title="Category Semantic Search", page_icon="🔎")
    st.title("Category Semantic Search Playground")
    st.write(
        "Enter a natural language description of an event to find the most relevant "
        "category definitions indexed in Typesense."
    )

    with st.sidebar:
        st.header("Configuration")
        if st.checkbox("Load from .env", value=True):
            load_dotenv()

        default_collection = os.environ.get("TYPESENSE_COLLECTION", "category_definitions")
        default_model = os.environ.get(
            "SEMANTIC_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        )

        host = st.text_input("Host", value=os.environ.get("TYPESENSE_HOST", "localhost"))
        port = st.number_input(
            "Port", value=int(os.environ.get("TYPESENSE_PORT", 8108)), step=1
        )
        protocol = st.selectbox(
            "Protocol", options=["http", "https"], index=0 if os.environ.get("TYPESENSE_PROTOCOL", "http") == "http" else 1
        )
        api_key = st.text_input(
            "API Key", value=os.environ.get("TYPESENSE_API_KEY", ""), type="password"
        )
        collection = st.text_input("Collection", value=default_collection)
        model_name = st.text_input("Embedding model", value=default_model)
        k = st.slider("Results", min_value=1, max_value=20, value=5)

    if not api_key:
        st.warning("Provide a Typesense API key to search.")
        return

    query = st.text_input("Search query", placeholder="e.g. Outdoor music festival with local bands")
    submitted = st.button("Search")

    if submitted and query:
        with st.spinner("Searching..."):
            model = get_model(model_name)
            client = get_client(host, int(port), protocol, api_key)
            embedding = model.encode([query], normalize_embeddings=True)[0]
            vector_query = f"embedding:([{format_embedding(embedding)}], k:{k})"
            search_parameters = {
                "q": query,
                "query_by": "category,definition",
                "vector_query": vector_query,
                "per_page": k,
            }
            response = client.collections[collection].documents.search(search_parameters)

        hits = response.get("hits", [])
        if not hits:
            st.info("No results found.")
            return

        for hit in hits:
            document = hit.get("document", {})
            score = hit.get("vector_distance", 0)
            st.subheader(document.get("category", "(no category)"))
            st.markdown(document.get("definition", "(no definition)"))
            st.caption(f"Vector distance: {score:.4f}")

            extras = {
                key: value
                for key, value in document.items()
                if key not in {"id", "category", "definition", "embedding"}
            }
            if extras:
                with st.expander("Additional fields"):
                    st.json(extras)


if __name__ == "__main__":
    main()

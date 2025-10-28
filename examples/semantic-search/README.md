# Semantic Search Playground for Event Categories

This example demonstrates how to build a semantic search experience for event categories using Typesense and sentence-transformer embeddings. It includes:

1. `process_categories.py` – convert an Excel workbook of categories and their descriptions to JSONL.
2. `index_categories.py` – generate embeddings and index the categories in a Typesense collection.
3. `app.py` – a Streamlit-based UI for querying the collection with natural language.

## Prerequisites

- Python 3.9 or later.
- A running Typesense server with vector search enabled (v0.25+).
- The [Python Typesense client](https://typesense.org/docs/latest/api/python.html) credentials (API key, host, port, protocol).
- Install the Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Tip:** Installing `sentence-transformers` will download the embedding model on the first run. If you're operating in an offline environment, download the model ahead of time and point the scripts to the local path.

## 1. Convert the Excel workbook to JSONL

Use `process_categories.py` to normalize your Excel workbook into newline-delimited JSON:

```bash
python process_categories.py \
  data/event_categories.xlsx \
  --sheet-name "Categories" \
  --category-column "Category" \
  --definition-column "Definition" \
  --metadata-columns "Example" "Notes" \
  --output categories.jsonl
```

The script expects the category and definition columns to be present. You can pass additional metadata columns that should be stored alongside each document.

## 2. Generate embeddings and index in Typesense

`index_categories.py` can ingest either the JSONL file created in the previous step or read directly from Excel.

### Using the JSONL output

```bash
python index_categories.py \
  --documents-path categories.jsonl \
  --collection category_definitions \
  --api-key ${TYPESENSE_API_KEY}
```

### Reading directly from Excel

```bash
python index_categories.py \
  --excel-path data/event_categories.xlsx \
  --sheet-name "Categories" \
  --category-column "Category" \
  --definition-column "Definition" \
  --collection category_definitions \
  --api-key ${TYPESENSE_API_KEY}
```

By default the script uses the `sentence-transformers/all-MiniLM-L6-v2` model and connects to `http://localhost:8108`. Override the host, port, protocol, collection name, or model with command-line arguments or environment variables (`TYPESENSE_HOST`, `TYPESENSE_PORT`, `TYPESENSE_PROTOCOL`, `TYPESENSE_API_KEY`, `TYPESENSE_COLLECTION`, `SEMANTIC_MODEL_NAME`).

## 3. Run the Streamlit search UI

Launch the Streamlit app to test natural-language queries against your indexed collection:

```bash
streamlit run app.py
```

In the sidebar you can configure:

- Typesense connection settings (host, port, protocol, API key, collection).
- The embedding model used for queries.
- The number of results (`k`).

> The API key is required to run searches. The app can load credentials from a `.env` file if `Load from .env` is checked.

Once the app is running, open the provided URL in your browser, enter a query such as "family-friendly outdoor music festival" and press **Search**. The results include the most similar categories along with their definitions and optional metadata.

## Resetting the collection

If you need to recreate the collection from scratch, delete it before re-running the indexing script:

```bash
python - <<'PY'
import typesense
client = typesense.Client({
    "nodes": [{"host": "localhost", "port": 8108, "protocol": "http"}],
    "api_key": "${TYPESENSE_API_KEY}",
    "connection_timeout_seconds": 5,
})
try:
    client.collections['category_definitions'].delete()
    print("Deleted existing collection")
except typesense.exceptions.ObjectNotFound:
    print("Collection did not exist")
PY
```

You can then rerun `index_categories.py` to rebuild the collection.

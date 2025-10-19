## RAG FastAPI

A minimal Retrieval-Augmented Generation (RAG) service built with FastAPI. It ingests documents (file upload or URL), chunks and embeds them, stores vectors in a JSON file, and answers questions grounded in retrieved context using Google Generative AI.

### Features
- Ingest via file upload or URL
- Parse txt, md, html, and pdf (text-extractable) files
- Simple JSON-based vector store and registry under `data/`
- Ask questions with citations to source chunks
- Health check and structured error handling

### Requirements
- Python 3.11+
- A Google Generative AI API key

### Quickstart
1) Clone and enter the project directory.
2) Create and activate a virtual environment:
```bash
python3 -m venv .venv && source .venv/bin/activate
```
3) Install dependencies:
```bash
pip install -r requirements.txt
```
4) Create a `.env` file:
```bash
cp .env.example .env  # if you create one; otherwise create manually
```

Minimum variables:
- `GOOGLE_API_KEY` (required for /ask)
- `LOG_LEVEL` (optional, default: INFO)
- `DEFAULT_WORKSPACE` (optional, default: "default")
- `MAX_UPLOAD_MB` (optional, default: 25)
- `GENERATION_MODEL` (optional, default: gemini-2.5-flash)

5) Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

### API

- `GET /health`
  - Returns `{ "ok": true }`.

- `POST /ingest/file` (multipart/form-data)
  - Fields:
    - `file`: UploadFile
    - `workspace` (optional): string
  - Response: `{ ok: true, fileId: string, chunks: number, workspace: string }`

- `POST /ingest/url` (application/json)
  - Body:
    - `fileUrl`: string (required)
    - `filename`: string (required)
    - `workspace` (optional): string
    - `fileId` (optional): string (client-supplied id)
  - Response: `{ ok: true, fileId: string, chunks: number, workspace: string }`

- `POST /ask` (application/json)
  - Body:
    - `q`: string (required)
    - `workspace` (optional, default `DEFAULT_WORKSPACE`)
    - `k` (optional, default 15)
  - Response: `{ answer: string, sources: { filename: string, chunkId: number }[] }`
  - Notes: Requires `GOOGLE_API_KEY`. Uses `GENERATION_MODEL`.

- `POST /delete` (application/json)
  - Body:
    - `fileId`: string (required)
  - Response: `{ ok: true, removed: number }`

### Data Storage
- `data/vec.json`: vector store of chunks and embeddings.
- `data/registry.json`: registry of ingested files and metadata.
Both files are created on first run; the `data/` directory is ignored by Git.

### Development
- Linting/formatting: add your preferred tools (e.g., ruff/black) as needed.
- Tests: add with `pytest` as desired. The project currently ships without tests.

### Troubleshooting
- 400 "Missing GOOGLE_API_KEY" on `/ask`: set `GOOGLE_API_KEY` in `.env`.
- 400 on ingest: file too large or unsupported type (scanned PDFs without text are not supported).
- Empty or low-quality answers: verify embeddings populated in `data/vec.json` and your API key has access to the selected model.

### License
MIT



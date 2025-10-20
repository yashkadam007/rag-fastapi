# Runbook (Manual Test)

## Prereqs
- Python venv activated; install deps: `pip install -r requirements.txt`
- Env vars:
  - `DATABASE_URL` (Postgres)
  - `GOOGLE_API_KEY` (for /ask)
  - Optional: `USE_JSON_VECTOR_STORE=true` to use file store
- Start API: `uvicorn app.main:app --reload`
- Create a user id: `export USER_ID=$(python -c 'import uuid;print(uuid.uuid4())')`
- Base curl flags: `-H "X-User-Id: $USER_ID" -H "Content-Type: application/json"`

## Flow
1) Health
```
curl http://localhost:8000/health
```

2) Create chat
```
curl -X POST http://localhost:8000/chats \
  -H "X-User-Id: $USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Chat"}'
```
Save `chatId` from the response.

3) Upload document (file)
```
curl -X POST http://localhost:8000/chats/$CHAT_ID/documents/file \
  -H "X-User-Id: $USER_ID" \
  -F file=@/path/to/file.pdf
```
Save `documentId`.

4) Ask a question (RAG)
```
curl -X POST http://localhost:8000/chats/$CHAT_ID/ask \
  -H "X-User-Id: $USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"q":"What does the document say about X?"}'
```
Expect `{ answer, sources }`.

5) List messages
```
curl http://localhost:8000/chats/$CHAT_ID/messages -H "X-User-Id: $USER_ID"
```

6) List documents
```
curl http://localhost:8000/chats/$CHAT_ID/documents -H "X-User-Id: $USER_ID"
```

7) Delete document
```
curl -X DELETE http://localhost:8000/documents/$DOCUMENT_ID -H "X-User-Id: $USER_ID"
```

8) Delete chat
```
curl -X DELETE http://localhost:8000/chats/$CHAT_ID -H "X-User-Id: $USER_ID"
```

## Reset DB
- If needed, drop tables and run Alembic:
```
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## Troubleshooting
- 401: ensure `X-User-Id` is a valid UUID.
- 400 upload: file too large; adjust `MAX_UPLOAD_MB`.
- 502 on ask: verify `GOOGLE_API_KEY`, model access, and outbound network.
  

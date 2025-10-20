# Backend Contracts (v0)

Auth: send header `X-User-Id: <uuidv4>` in all requests.

## Entities
- User: UUID
- Chat: `{ id, title, createdAt, updatedAt }`
- Document: `{ id, filename, sizeBytes, numChunks, indexed, createdAt, updatedAt }`
- Message: `{ id, role: 'user'|'assistant'|'system'|'tool', content, createdAt }`

## Endpoints

### Health
- GET `/health` → `{ ok: true, db: boolean }`

### Chats
- POST `/chats`
  - body: `{ "title": string }`
  - resp: `{ id, title, createdAt, updatedAt }`
- GET `/chats`
  - resp: `[ { id, title, createdAt, updatedAt } ]`
- GET `/chats/{chatId}`
  - resp: `{ id, title, createdAt, updatedAt }`
- DELETE `/chats/{chatId}`
  - resp: `{ ok: true }`

### Documents
- GET `/chats/{chatId}/documents`
  - resp: `[ Document ]`
- POST `/chats/{chatId}/documents/file` (multipart)
  - fields: `file: File`
  - resp: `{ ok: true, documentId, chunks }`
- POST `/chats/{chatId}/documents/url`
  - body: `{ fileUrl: string, filename: string }`
  - resp: `{ ok: true, documentId, chunks }`
- DELETE `/documents/{documentId}`
  - resp: `{ ok: true, removed: number }`

### Messages & Ask
- GET `/chats/{chatId}/messages?limit=&before=`
  - resp: `[ Message ]` (ascending by time)
- POST `/chats/{chatId}/messages`
  - body: `{ content: string }`
  - resp: `Message`
- POST `/chats/{chatId}/ask`
  - body: `{ q: string, k?: number }`
  - resp: `{ answer: string, sources: [{ filename, chunkId }] }`

## Error model
On error, FastAPI default structure or `{ "detail": string }`.

## Notes
- All IDs are UUIDv4 strings.
- Only documents attached to a chat are used for retrieval in that chat.


# Backend Contracts (v0)

Auth: Cookie-based session. On sign-in/sign-up, server sets `Set-Cookie: session=<token>; HttpOnly; Secure; SameSite=Lax`. Send cookies with requests.

## Entities
- User: `{ id, email, name?, createdAt, updatedAt }`
- Account: `{ id, userId, emailVerified, createdAt, updatedAt }`
- Session: `{ id, userId, createdAt, expiresAt, revokedAt? }`
- Chat: `{ id, title, createdAt, updatedAt }`
- Document: `{ id, filename, sizeBytes, numChunks, indexed, createdAt, updatedAt }`
- Message: `{ id, role: 'user'|'assistant'|'system'|'tool', content, createdAt }`

## Endpoints
### Auth
- POST `/auth/sign-up`
  - body: `{ email: string, password: string, name?: string }`
  - resp: `{ ok: true, userId, email, name }` (sets session cookie)
- POST `/auth/sign-in`
  - body: `{ email: string, password: string }`
  - resp: `{ ok: true, userId, email, name }` (sets session cookie)
- POST `/auth/sign-out`
  - resp: `{ ok: true }` (clears session cookie)

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
- Auth required for all endpoints except `/health` and `/auth/*`.


## Next.js Auth Integration (Cookie Sessions)

This backend issues HttpOnly, Secure session cookies on `/auth/sign-in` and `/auth/sign-up`. Use the steps below to integrate in a Next.js (App Router) app.

### 1) Sign Up
```ts
// app/(auth)/sign-up/actions.ts
"use server";

export async function signUp(data: { email: string; password: string; name?: string }) {
  const res = await fetch(process.env.API_URL + "/auth/sign-up", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(data),
    // Cookies are set by the server via Set-Cookie; no client handling required
  });
  if (!res.ok) throw new Error("Sign up failed");
  return (await res.json()) as { ok: true; userId: string; email: string; name?: string };
}
```

### 2) Sign In
```ts
// app/(auth)/sign-in/actions.ts
"use server";

export async function signIn(email: string, password: string) {
  const res = await fetch(process.env.API_URL + "/auth/sign-in", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password }),
    // On Vercel/Next, this will forward and store HttpOnly cookie in the browser
  });
  if (!res.ok) throw new Error("Invalid credentials");
  return (await res.json()) as { ok: true; userId: string; email: string; name?: string };
}
```

### 3) Sign Out
```ts
// app/(auth)/sign-out/actions.ts
"use server";

export async function signOut() {
  const res = await fetch(process.env.API_URL + "/auth/sign-out", { method: "POST" });
  if (!res.ok) throw new Error("Sign out failed");
}
```

### 4) Calling Protected APIs from Next.js

- Client components: fetch normally; the browser will send cookies automatically to same-site API. If cross-origin, set `credentials: "include"` and configure CORS.
```ts
await fetch(process.env.NEXT_PUBLIC_API_URL + "/chats", { credentials: "include" });
```

- Server components/actions/route handlers: forward cookies to the backend when the backend is on a different origin.
```ts
import { cookies } from "next/headers";

export async function getChats() {
  const cookieStore = cookies();
  const cookieHeader = cookieStore.toString(); // serialize all cookies
  const res = await fetch(process.env.API_URL + "/chats", {
    headers: { cookie: cookieHeader },
  });
  if (!res.ok) throw new Error("Failed to fetch chats");
  return (await res.json()) as { id: string; title: string; createdAt: number; updatedAt: number }[];
}
```

### 5) CORS and Cookies

If your Next.js app runs on a different domain, enable CORS in FastAPI with credentials allowed and same-site cookie policy compatible with your deployment:

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

Ensure your frontend fetches set `credentials: "include"` for cross-origin requests.

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
  

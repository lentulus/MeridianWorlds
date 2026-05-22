# Server Language Comparison: Python / FastAPI vs TypeScript

*2026-05-21*

Scope: choosing the backend language for the Worlds visualisation server. The client
is a Three.js app written in TypeScript (not yet implemented). Three criteria drive
the comparison: cross-platform availability, interface quality with the TypeScript
client, and Claude's ability to produce specification-conformant code. This document
adds VS Code development experience, deployment to a remote server or AWS, and the
question of whether the server can serve the client app.

Go and Rust are excluded — they offer no advantage for a data-access server at this
scale and their schema-generation story for TypeScript clients is significantly weaker.

---

## 1. Cross-platform availability

Both work identically on Mac and Ubuntu.

| | Mac | Ubuntu |
|---|---|---|
| Python / FastAPI | `brew install python` or system Python | `apt install python3`, or pyenv |
| TypeScript / Node | `brew install node`, or nvm | `apt install nodejs`, or nvm |

No meaningful difference. Both are universally available and stable.

---

## 2. Interface with the TypeScript client

This is the most important criterion for an ongoing project.

### Python / FastAPI

FastAPI generates an OpenAPI 3.1 schema automatically from Pydantic models. A
one-command code-generation step produces TypeScript types:

```
openapi-typescript http://localhost:8000/openapi.json --output client/src/api.d.ts
```

Or with `hey-api` for typed fetch functions. The Pydantic model is the single source
of truth; the TypeScript types are derived artefacts. Any mismatch between server and
client is caught at generation time, not at runtime in the browser.

The process requires running the generation step after any model change. In practice
this means adding `npm run gen:types` to the dev workflow.

### TypeScript

Server and client are the same language. Type definitions can live in a shared
package and be imported directly by both:

```
worlds/
  packages/
    shared/
      src/types.ts      ← one definition, used by server and client
    server/
      src/routes/...
    client/
      src/...
```

Using pnpm workspaces (or npm workspaces), both packages import from `@worlds/shared`.
There is no generation step, no artefact to commit, no script to forget to run. A
type change in `types.ts` immediately produces a compile error in every consumer —
server routes, client fetch calls, and component props — simultaneously.

**Verdict:** TypeScript's shared-type model is strictly cleaner. FastAPI's generated
types are a good substitute and adequate for a small API surface, but shared types
eliminate an entire class of synchronisation error.

---

## 3. Claude code quality

### Python / FastAPI

FastAPI + Pydantic is one of the most thoroughly represented stacks in Claude's
training data. Route definitions, response models, dependency injection, and validation
error handling follow one idiomatic pattern. Claude reproduces it reliably even for
complex schemas. Pydantic enforces the schema at runtime — a shape error becomes a
422 response rather than a silent wrong value reaching the client.

### TypeScript (Hono or Fastify)

Claude writes correct TypeScript servers. Hono is the recommended choice: it runs on
Node.js, Bun, and AWS Lambda with identical code (important for deployment, below).
Zod is the runtime validation equivalent of Pydantic and is equally well-represented
in Claude's training data. The shared-type advantage compounds with Claude: a single
type definition drives server validation, route handler types, and client consumption,
so Claude can be asked to update all three consistently in one prompt.

**Verdict:** roughly equal. Python's runtime validation via Pydantic is arguably
harder to get wrong. TypeScript's static typing catches more errors before the server
starts. For spec-driven iterative work with Claude, TypeScript's unified type model
means fewer opportunities for the spec and the code to diverge silently.

---

## 4. VS Code development experience

### Python / FastAPI

- **Pylance** (Microsoft): strong type inference, good completion, inline errors.
- **Python Debugger** extension: set breakpoints in route handlers, step through
  Pydantic validators, inspect request state.
- `uvicorn --reload` restarts the server on file save; not as fast as HMR but
  adequate for an API server.
- Two terminal tabs: one for uvicorn, one for the Vite client dev server.
- Pylance infers return types from Pydantic models but inference across files can
  miss errors that mypy catches — running mypy in the terminal is a separate step.

### TypeScript

- **TypeScript language server** is built into VS Code — no extension required. This
  is the reference implementation: the fastest, most complete, and most reliable.
- Inline errors appear as you type, including across the shared types package.
  Renaming a field in `types.ts` immediately underlines every consumer with a
  compile error before any file is saved.
- **ts-node-dev** or **tsx --watch** hot-reloads the server on save with no restart
  overhead.
- Debugging via the built-in Node debugger (launch config in `.vscode/launch.json`);
  breakpoints work identically to Python.
- One `package.json` workspace can define `dev` scripts that start both server and
  Vite client with a single `pnpm dev` command (using `concurrently`).

**Verdict:** TypeScript's VS Code experience is better. The language server is the
canonical one; errors are caught inline across the whole codebase, including the
client. The monorepo `dev` script is a quality-of-life improvement that Python
cannot match without a Makefile or `overmind`.

---

## 5. Deployment

### Local / self-managed server (VPS, EC2 with SSH access)

**Python / FastAPI**

```
# Production process
gunicorn server.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

Run behind nginx as a reverse proxy. Use systemd to manage the process. Standard,
well-documented, production-grade.

**TypeScript / Hono**

```
# Production process
node dist/server.js
```

Or use **PM2** for process management (`pm2 start dist/server.js --name worlds`).
Same nginx + systemd pattern. Node.js servers are equally standard on VPS deployments.

Both are equivalent for this scenario.

---

### AWS (Lambda, App Runner, ECS)

**Python / FastAPI**

Lambda requires the **Mangum** adapter to wrap the ASGI app:

```python
from mangum import Mangum
handler = Mangum(app)
```

Works, but Mangum is a third-party shim and adds a cold-start penalty. App Runner and
ECS Fargate (Docker container) work without any adapter — FastAPI runs exactly as it
does locally.

**TypeScript / Hono**

Hono is designed for this. Its runtime target is selected at import time:

```typescript
// Lambda
import { handle } from 'hono/aws-lambda'
export const handler = handle(app)

// Node.js (local, ECS, App Runner)
import { serve } from '@hono/node-server'
serve(app)
```

The same route code runs unmodified on Lambda, Node, and Bun. No third-party adapter;
the runtime abstraction is built into Hono's design. Cold starts are lower than
Python because Node.js initialises faster than a full CPython + uvicorn stack.

For **AWS Lambda specifically**, TypeScript with Hono is the cleaner path. For
**ECS or App Runner** (long-running container), both are equivalent.

---

## 6. Serving the client TypeScript app

Both server options can serve the compiled Three.js client. The recommended pattern
is the same regardless of server language.

### Development

Run two processes: the API server and the Vite development server. Vite proxies
`/api/*` requests to the API server so the client fetches data without CORS issues.

```javascript
// client/vite.config.ts
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
}
```

Vite's HMR (hot module replacement) updates the browser instantly on client file
changes. The API server restarts independently on its own file changes. The two
processes are independent; either can be restarted without affecting the other.

With a TypeScript monorepo, a single `pnpm dev` can start both:

```json
// package.json (root)
"scripts": {
  "dev": "concurrently \"pnpm --filter server dev\" \"pnpm --filter client dev\""
}
```

With Python, the equivalent is a `Makefile` target or `overmind`/`foreman`.

### Production

Build the client to a static bundle and serve it from the API server.

**FastAPI:**

```python
from fastapi.staticfiles import StaticFiles

# After all API routes are registered:
app.mount("/", StaticFiles(directory="client/dist", html=True), name="client")
```

All unmatched routes fall through to `index.html`, which is correct for a
single-page app with client-side routing.

**Hono / Node:**

```typescript
import { serveStatic } from '@hono/node-server/serve-static'

app.use('/*', serveStatic({ root: '../client/dist' }))
```

Both approaches work. The result is one server process and one port in production,
which simplifies deployment (no separate nginx needed for static files on a VPS).

### AWS deployment with static files

For AWS, the preferred pattern is to separate concerns:

- **API server** → Lambda function or ECS container (the Python or TypeScript server)
- **Static client** → S3 bucket + CloudFront CDN

This gives the client global CDN caching and removes the static-file burden from the
API server entirely. The client fetches `/api/*` from the API server's URL (configured
as an environment variable at build time).

---

## 7. Summary

| | Python / FastAPI | TypeScript (Hono) |
|---|---|---|
| Mac + Ubuntu | ✓ | ✓ |
| TS client interface | OpenAPI → generated types | Shared types, no generation step |
| Claude code quality | Excellent | Excellent |
| VS Code experience | Good (Pylance) | Best (native TS server) |
| VPS / self-hosted | gunicorn + nginx | PM2 / node + nginx |
| AWS Lambda | Mangum adapter required | Native (Hono built-in) |
| AWS ECS / App Runner | Docker, no adapter | Docker, no adapter |
| Serves client app | StaticFiles mount | serveStatic middleware |
| Existing codebase | Already in use | New runtime |

---

## Recommendation

**If the project stays small and Python-only** (world generation scripts, SQLite
access, Meridian API layer all in Python already): stay with FastAPI. The OpenAPI
→ TypeScript generation step is a minor inconvenience; the existing toolchain
investment is real; and Claude writes excellent FastAPI code.

**If the Three.js client becomes complex** — frequent schema changes, real-time
WebSocket streams, TypeScript types shared across many components — switch to
TypeScript (Hono). The shared-type model eliminates synchronisation errors, the VS
Code experience is better, and AWS Lambda deployment is simpler. The cost is
introducing a second runtime (Node.js) and rewriting the existing server routes.

A pragmatic middle path: keep the Python server for now, add the `openapi-typescript`
generation step to the client build, and revisit the decision once the client is
substantially implemented and the friction of type synchronisation becomes measurable.

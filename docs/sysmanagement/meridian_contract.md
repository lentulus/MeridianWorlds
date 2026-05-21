# Meridian API Contract — Governance Design

*2026-05-10*

---

## Principle

Meridian is the sole owner of its data contract. Consumer projects (Worlds, and any future campaign tools) **import from Meridian; they never copy or redefine its models.**

---

## Project layout

```
~/projects/
  meridian/
    meridian/
      api.py          ← canonical function signatures
      models.py       ← canonical Pydantic models
    API_REQUESTS.md   ← where consumers file change proposals
    CHANGELOG.md      ← breaking and additive changes, versioned
  worlds/
    meridian/         ← local shim only; imports from the real meridian package
      api.py
      models.py
```

Until Meridian is packaged and installable, the Worlds project imports from its local `meridian/` shim, which in turn delegates to the real Meridian package via `sys.path` or an editable install. The shim must not define any models or logic — only re-exports.

---

## Why Pydantic for the contract

Meridian returns raw JSON. The single translation from `dict` to typed object happens once, at the boundary in `meridian/api.py`:

```python
def get_body(body_id: str) -> Body:
    raw: dict = _call("get_body", body_id)
    return Body.model_validate(raw)   # raises ValidationError on bad data
```

After that call, all downstream code uses attribute access (`body.gravity_g`), gets IDE autocompletion, and is protected from silent key errors. The consumer never sees the raw dict.

Pydantic reference: https://docs.pydantic.dev/latest/concepts/models/

---

## How to request an API change

An AI working in a consumer project (e.g. Worlds) that needs a new field or endpoint writes a proposal to `meridian/API_REQUESTS.md`. It does not modify `meridian/models.py` or `meridian/api.py` directly.

Template:

```markdown
## Request: <short title>
**Requester:** worlds
**Date:** YYYY-MM-DD
**Need:** What data the consumer requires that is not currently exposed.
**Proposed change:** New field / new function signature / modified return type.
**Rationale:** Why Meridian should own this data rather than the consumer deriving it.
**Status:** PROPOSED
```

Status values: `PROPOSED` → `ACCEPTED` / `REJECTED` / `DEFERRED`

When Meridian implements the change it updates the status, bumps `CHANGELOG.md`, and the consumer updates its usage.

---

## Rules for consumer projects

1. Import models from `meridian.models`, not from `meridian.api`.
2. Never define a local dataclass or TypedDict that duplicates a Meridian model.
3. If a field is missing, file a request — do not patch the object locally.
4. Treat `ValidationError` from `model_validate` as a hard failure; it means Meridian's output changed without notice.

---

## CLAUDE.md entries

**In Worlds** (`worlds/CLAUDE.md`):

```
## Meridian API
- Import from `meridian/api.py` and `meridian/models.py` — never copy or redefine these.
- To request an API change: append to `../meridian/API_REQUESTS.md` using the template in `docs/meridian_contract.md`.
```

**In Meridian** (`meridian/CLAUDE.md`):

```
## API contract
- `meridian/api.py` and `meridian/models.py` are the canonical contract.
- Pending change requests: `API_REQUESTS.md`.
- Record every breaking or additive change in `CHANGELOG.md`.
```

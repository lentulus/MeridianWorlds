"""
generate_species_md.py

Reads alien species records from world.db, fetches homeworld context from the
Meridian API, submits a Claude Batch API request to generate Obsidian .md files
for each species, and writes the results to the Obsidian vault.

USAGE
-----
    python3 lifeforms/scripts/generate_species_md.py [options]

    --roles         Comma-separated campaign roles to include (default: PEOPLE,BEAST)
    --vault-dir     Obsidian species output dir (default: ~/projects/reference/worldbuild/species/)
    --batch-id      Resume polling an existing batch rather than creating a new one
    --dry-run       Print first 3 requests to stdout without calling the API
    --force         Overwrite existing .md files (default: skip)

DEPENDENCIES
------------
    pip install anthropic pydantic

    ANTHROPIC_API_KEY must be set in the environment.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from textwrap import dedent

import anthropic

import meridian.api as meridian_api
from config import WORLDS_DB

# ── Paths ─────────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
PROMPT_FILE = _HERE.parent / "prompts" / "species_system_prompt.md"

DEFAULT_VAULT_DIR = Path.home() / "projects" / "reference" / "worldbuild" / "species"

# ── Model selection ───────────────────────────────────────────────────────────

MODEL_BY_ROLE = {
    "PEOPLE":  "claude-opus-4-7",
    "BEAST":   "claude-sonnet-4-6",
    "THING":   "claude-haiku-4-5-20251001",
    "MONSTER": "claude-haiku-4-5-20251001",
}

MAX_TOKENS_BY_ROLE = {
    "PEOPLE":  2048,
    "BEAST":   1200,
    "THING":   800,
    "MONSTER": 800,
}

# ── Data fetch ────────────────────────────────────────────────────────────────

def fetch_species(roles: list[str]) -> list[dict]:
    placeholders = ",".join("?" * len(roles))
    conn = sqlite3.connect(WORLDS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT * FROM species WHERE campaign_role IN ({placeholders})"
        f" ORDER BY campaign_role, name",
        roles,
    ).fetchall()
    conn.close()

    records = []
    for row in rows:
        record = dict(row)
        if record.get("body_id"):
            body = meridian_api.get_body(record["body_id"])
            record["homeworld_name"] = body.name
            record["system_id"]      = body.system_id
            record["gravity_g"]      = body.gravity_g
            record["atm_pressure_bar"] = body.atm_pressure_bar
            record["mean_temp_k"]    = body.mean_temp_k
            record["hydrosphere_pct"] = body.hydrosphere_pct
            record["volatile_type"]  = body.volatile_type
        records.append(record)
    return records


# ── Prompt construction ───────────────────────────────────────────────────────

def load_system_prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def species_to_yaml(row: dict) -> str:
    """Serialise a species row + homeworld data as YAML for the user message."""
    skip = {"notes"}  # omit free-text input; Claude invents prose from structured fields
    lines = ["species_data:"]
    for k, v in row.items():
        if k in skip or v is None:
            continue
        lines.append(f"  {k}: {json.dumps(v)}")
    return "\n".join(lines)


def build_user_message(row: dict) -> str:
    role = row.get("campaign_role", "BEAST")
    role_instruction = (
        "Write a PEOPLE entry (sapient species)."
        if role == "PEOPLE"
        else f"Write a {role} entry."
    )
    return dedent(f"""\
        {role_instruction}

        {species_to_yaml(row)}
    """)


# ── Batch request assembly ────────────────────────────────────────────────────

def build_batch_requests(
    species: list[dict],
    system_prompt: str,
    vault_dir: Path,
    force: bool,
) -> list[dict]:
    requests = []
    for row in species:
        slug = row.get("obsidian_slug") or row["species_id"]
        out_path = vault_dir / f"{slug}.md"
        if out_path.exists() and not force:
            print(f"  skip (exists): {out_path.name}")
            continue

        role = row.get("campaign_role", "BEAST")
        model = MODEL_BY_ROLE.get(role, "claude-sonnet-4-6")

        requests.append({
            "custom_id": slug,
            "params": {
                "model": model,
                "max_tokens": MAX_TOKENS_BY_ROLE.get(role, 1200),
                "thinking": {"type": "adaptive"},
                "system": [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                "messages": [
                    {"role": "user", "content": build_user_message(row)},
                ],
            },
        })
    return requests


# ── Batch lifecycle ───────────────────────────────────────────────────────────

POLL_INTERVAL = 60  # seconds


def submit_batch(client: anthropic.Anthropic, requests: list[dict]) -> str:
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch created: {batch.id}  ({len(requests)} requests)")
    return batch.id


def wait_for_batch(client: anthropic.Anthropic, batch_id: str) -> None:
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(
            f"  [{batch.processing_status}] "
            f"processing={counts.processing} "
            f"succeeded={counts.succeeded} "
            f"errored={counts.errored} "
            f"canceled={counts.canceled} "
            f"expired={counts.expired}"
        )
        if batch.processing_status == "ended":
            break
        time.sleep(POLL_INTERVAL)


def write_results(
    client: anthropic.Anthropic,
    batch_id: str,
    vault_dir: Path,
    force: bool,
) -> tuple[int, int]:
    vault_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    errors = 0
    for result in client.messages.batches.results(batch_id):
        slug = result.custom_id
        out_path = vault_dir / f"{slug}.md"

        if result.result.type == "succeeded":
            content = result.result.message.content
            text_blocks = [b.text for b in content if hasattr(b, "text")]
            md_text = "\n".join(text_blocks).strip()

            if out_path.exists() and not force:
                print(f"  skip (exists): {out_path.name}")
                continue

            out_path.write_text(md_text + "\n", encoding="utf-8")
            print(f"  wrote: {out_path.name}")
            written += 1

        elif result.result.type == "errored":
            err = result.result.error
            print(
                f"  ERROR [{slug}]: {err.type} — {getattr(err, 'message', '')}",
                file=sys.stderr,
            )
            errors += 1

    return written, errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Obsidian species .md files via Claude Batch API"
    )
    parser.add_argument(
        "--roles", default="PEOPLE,BEAST",
        help="Comma-separated campaign roles (default: PEOPLE,BEAST)",
    )
    parser.add_argument(
        "--vault-dir", type=Path, default=DEFAULT_VAULT_DIR,
        help="Obsidian species output directory",
    )
    parser.add_argument(
        "--batch-id", default=None,
        help="Resume polling an existing batch (skips fetch and submission)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print first 3 requests to stdout without calling the API",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing .md files",
    )
    args = parser.parse_args()

    roles = [r.strip().upper() for r in args.roles.split(",")]
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        sys.exit("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key) if not args.dry_run else None
    system_prompt = load_system_prompt()

    if args.batch_id:
        print(f"Resuming batch {args.batch_id} ...")
        wait_for_batch(client, args.batch_id)
        written, errors = write_results(client, args.batch_id, args.vault_dir, args.force)
        print(f"\nDone: {written} written, {errors} errors.")
        return

    print(f"Fetching species ({', '.join(roles)}) from {WORLDS_DB} ...")
    species = fetch_species(roles)
    print(f"  {len(species)} species found.")

    if not species:
        print("Nothing to do.")
        return

    requests = build_batch_requests(species, system_prompt, args.vault_dir, args.force)
    print(f"  {len(requests)} requests to submit (skipped {len(species) - len(requests)}).")

    if args.dry_run:
        for req in requests[:3]:
            print(json.dumps(req, indent=2))
        if len(requests) > 3:
            print(f"  ... and {len(requests) - 3} more.")
        return

    if not requests:
        print("All species already have .md files. Use --force to regenerate.")
        return

    batch_id = submit_batch(client, requests)
    wait_for_batch(client, batch_id)
    written, errors = write_results(client, batch_id, args.vault_dir, args.force)
    print(f"\nDone: {written} written, {errors} errors.")


if __name__ == "__main__":
    main()

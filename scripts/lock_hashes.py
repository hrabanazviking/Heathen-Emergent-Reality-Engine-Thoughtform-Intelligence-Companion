"""
One-shot hash-locking script for the Mímisbrunnr Norse starter pack.

Downloads each source listed in NORSE_STARTER_PACK, computes the SHA-256
digest from the streamed bytes, and prints a line per source:

    <source_id>: <hex_digest>  (<url>)

Run from the repo root:
    python scripts/lock_hashes.py

The output is machine-readable: paste the five hex strings into
src/heretic/skilningr/mimisbrunnr/manifest.py, one per sha256 field.
"""

import asyncio
import hashlib
import sys
from pathlib import Path

# Allow import from src/ without an install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx  # noqa: E402

from heretic.skilningr.mimisbrunnr.manifest import NORSE_STARTER_PACK  # noqa: E402


async def fetch_hash(source, client: httpx.AsyncClient) -> tuple[str, str | None, str]:
    """Stream-download source.url, compute SHA-256, return (id, hex, url)."""
    h = hashlib.sha256()
    try:
        async with client.stream("GET", source.url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(65536):
                h.update(chunk)
        return source.id, h.hexdigest(), source.url
    except Exception as exc:  # noqa: BLE001
        return source.id, None, f"FAILED: {exc}"


async def main() -> None:
    print("Mímisbrunnr SHA-256 hash locking — streaming five sources...\n")
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(300.0, connect=30.0),
        follow_redirects=True,
        headers={"User-Agent": "HERETIC-hashlock/1.0 (https://github.com/hrabanazviking)"},
    ) as client:
        for source in NORSE_STARTER_PACK.sources:
            sid, digest, url = await fetch_hash(source, client)
            if digest:
                print(f"{sid}: {digest}  ({url})")
            else:
                print(f"{sid}: FAILED  ({url})")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())

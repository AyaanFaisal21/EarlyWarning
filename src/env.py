"""Load .env from the project root.

Hand-rolled rather than depending on python-dotenv: it is fifteen lines, and one fewer
package to fail resolving at 11am.

`.env` is gitignored. Put keys there — never in a commit, never pasted into a chat, never
as a shell export (a fresh shell won't see it).
"""

from __future__ import annotations

import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def load(path: pathlib.Path = ENV_FILE, override: bool = False) -> list[str]:
    """Read KEY=VALUE lines into os.environ. Returns the names it set.

    A real environment variable wins over the file unless override=True — so you can
    temporarily point at a different key without editing anything.
    """
    if not path.exists():
        return []

    loaded = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and (override or key not in os.environ):
            os.environ[key] = value
            loaded.append(key)
    return loaded


def fix_ssl() -> str | None:
    """Point the stdlib at certifi's CA bundle.

    python.org builds on macOS ship without the system trust store, so anything using
    stdlib ssl/urllib fails certificate verification while curl succeeds. Setting
    SSL_CERT_FILE fixes every caller at once rather than threading a context through each
    call site. Respects an existing value.
    """
    if os.environ.get("SSL_CERT_FILE"):
        return os.environ["SSL_CERT_FILE"]
    try:
        import certifi
    except ImportError:
        return None
    bundle = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    return bundle


def status() -> str:
    """Which credentials are present, without revealing any of them."""
    rows = []
    for key, need in [
        ("TL_API_KEY", "TwelveLabs — extraction and embeddings"),
        ("TL_INDEX_ID", "TwelveLabs index (auto-created if absent)"),
        ("OPENAI_API_KEY", "OpenAI — pattern reasoning"),
        ("AWS_REGION", "AWS — Bedrock agent, S3 footage"),
    ]:
        v = os.environ.get(key)
        mark = f"set  ...{v[-4:]}" if v else "unset"
        rows.append(f"  {key:16s} {mark:14s} {need}")
    return "\n".join(rows)


load()
fix_ssl()


if __name__ == "__main__":
    print(f"reading {ENV_FILE}\n" if ENV_FILE.exists() else f"no {ENV_FILE}\n")
    print(status())
    print(f"\n  SSL bundle       {os.environ.get('SSL_CERT_FILE', 'system default')}")

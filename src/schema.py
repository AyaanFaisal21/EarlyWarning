"""Apply schema.cypher to whatever NEO4J_URI points at.

    python src/schema.py            # apply
    python src/schema.py --show     # list what exists

Replaces the `docker exec ... cypher-shell < schema.cypher` one-liner, which only worked
against the local container. Same file now applies to Aura, to Docker, or to anything else,
so switching targets is a single .env edit rather than a different command.
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(__file__))

from loader import Graph  # noqa: E402

SCHEMA_FILE = pathlib.Path(__file__).resolve().parent.parent / "schema.cypher"


def statements(path: pathlib.Path = SCHEMA_FILE) -> list[str]:
    """Split the file into executable statements, dropping comments.

    Neo4j's driver rejects multiple statements in one call, so they have to be sent
    individually — cypher-shell was doing this splitting for us.
    """
    body = "\n".join(
        line for line in path.read_text().splitlines() if not line.strip().startswith("//")
    )
    return [s.strip() for s in body.split(";") if s.strip()]


def apply(graph: Graph) -> tuple[int, list[str]]:
    applied, failed = 0, []
    for stmt in statements():
        try:
            graph.run(stmt)
            applied += 1
        except Exception as exc:
            failed.append(f"{stmt.splitlines()[0][:60]}... -> {type(exc).__name__}: {exc}")
    return applied, failed


def show(graph: Graph) -> str:
    out = []
    for label, query in [
        ("constraints", "SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties "
                        "RETURN name, labelsOrTypes, properties ORDER BY name"),
        ("indexes", "SHOW INDEXES YIELD name, type, labelsOrTypes, properties "
                    "RETURN name, type, labelsOrTypes, properties ORDER BY type, name"),
    ]:
        rows = graph.run(query)
        out.append(f"\n{label} ({len(rows)}):")
        for r in rows:
            props = ",".join(r.get("properties") or [])
            lbls = ",".join(r.get("labelsOrTypes") or [])
            kind = f" [{r['type']}]" if "type" in r else ""
            out.append(f"  {r['name']:24s}{kind:16s} ({lbls}) {props}")
    return "\n".join(out)


def main() -> None:
    graph = Graph()
    try:
        print(f"target: {os.environ.get('NEO4J_URI')}")
        if "--show" in sys.argv:
            print(show(graph))
            return

        applied, failed = apply(graph)
        print(f"applied {applied} statements")
        for f in failed:
            print(f"  FAILED  {f}")
        if failed:
            sys.exit(1)
        print(show(graph))
    finally:
        graph.close()


if __name__ == "__main__":
    main()

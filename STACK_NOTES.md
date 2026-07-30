# Stack Research — Video Agent Context Graph

Researched 2026-07-30, ahead of the hackathon. Verified against primary docs, not memory.
Anything marked **[VERIFY]** changed recently or had conflicting sources — confirm on the day.

---

## 0. The one architectural insight

**Pegasus (TwelveLabs) can emit graph-shaped JSON directly.** It does structured output
against a JSON Schema you supply, with real timestamps. So the naive pipeline —

    video → transcript → OpenAI extracts entities → Neo4j

is the wrong shape. It throws away everything non-verbal and burns your budget on an
extraction step you don't need. The right shape is:

    video → Pegasus (structured JSON: scenes+entities+tags, timestamped) → Neo4j
                  ↘ Marengo (512-d embeddings per segment) → Neo4j vector index
    OpenAI reasons OVER the assembled graph (NL → Cypher, multi-hop), it does not build it.

This matters for scoping: extraction is one API call with a good schema, not a subsystem.

---

## 1. TwelveLabs

`pip install twelvelabs`

```python
from twelvelabs import TwelveLabs
client = TwelveLabs(api_key="...")
```

### The upload flow changed — it's now two steps

Old tutorials show `client.task.create(index_id, file=...)`. That's gone. Current flow:

```python
# 1. create an index (once)
index = client.indexes.create(
    index_name="hackathon",
    models=[
        {"model_name": "marengo3.0", "model_options": ["visual", "audio"]},  # search/embed
        {"model_name": "pegasus1.2", "model_options": ["visual", "audio"]},  # generate
    ],
)

# 2. create an ASSET (upload)
asset = client.assets.create(method="url", url="https://...")
# or: client.assets.create(method="direct", file=open("clip.mp4", "rb"))

# 3. poll asset readiness (needed for files >200MB)
while client.assets.retrieve(asset.id).status != "ready":
    time.sleep(5)

# 4. INDEX the asset into the index
ia = client.indexes.indexed_assets.create(index_id=index.id, asset_id=asset.id)

# 5. poll indexing
while client.indexes.indexed_assets.retrieve(
        index_id=index.id, indexed_asset_id=ia.id).status != "ready":
    time.sleep(5)
```

Asset ≠ indexed asset. Two IDs, two polls. Budget for this — indexing is the slow step and
it is the thing that will eat your morning if you discover it at 11am.

### Structured output — the money feature

```python
from twelvelabs.types import AnalyzePromptV2, SyncResponseFormat, VideoContext_AssetId

text = client.analyze(
    model_name="pegasus1.5",
    video=VideoContext_AssetId(asset_id="..."),
    prompt_v_2=AnalyzePromptV2(input_text="Segment this video and extract entities."),
    response_format=SyncResponseFormat(
        type="json_schema",
        json_schema={
            "$defs": {
                "Chapter": {
                    "type": "object",
                    "properties": {
                        "chapter_title":   {"type": "string"},
                        "chapter_summary": {"type": "string"},
                        "chapter_number":  {"type": "integer"},
                        "start":           {"type": "number"},   # seconds
                        "end":             {"type": "number"},
                    },
                    "required": ["chapter_title","chapter_summary","chapter_number","start","end"],
                }
            },
            "type": "object",
            "properties": {"chapters": {"type": "array", "items": {"$ref": "#/$defs/Chapter"}}},
            "required": ["chapters"],
        },
    ),
)
data = json.loads(text.data)
```

Schema takes precedence over the prompt. Extend `Chapter` with `entities`, `tags`,
`on_screen_text` and you get your whole graph payload in one call.

**[VERIFY]** The SDK README shows a simpler `client.analyze(video_id=..., prompt=...)`;
the structured-responses doc shows `model_name=`/`video=VideoContext_AssetId(...)`, and
names `pegasus1.5` where index creation names `pegasus1.2`. Two call shapes and two version
strings in the same docs — check which the starter template uses before writing against it.

### Simple search (no schema needed)

```python
r = client.search.query(index_id=index.id, query_text="...", search_options=["visual","audio"])
```

### Gotchas
- `/gist` and `/summarize` endpoints **removed 2026-02-15**. Use `/analyze`. Most blog
  tutorials you'll find predate this and will not run.
- Marengo 2.7 **sunset 2026-03-30** — must use `marengo3.0`.
- Pegasus 1.5: context 261,120 tokens, max response 98,304. Sync analysis now supported
  (used to be async-only). Clip with `start_time`/`end_time`.
- **Marengo 3.0 embeddings are 512-dim** (2.7 was 1024). This is the number your Neo4j
  vector index needs. Getting it wrong = silent index mismatch.

---

## 2. Neo4j

### Vector index — version-sensitive, read carefully

```cypher
CREATE VECTOR INDEX scene_embedding IF NOT EXISTS
FOR (s:Scene) ON (s.embedding)
OPTIONS { indexConfig: {
  `vector.dimensions`: 512,
  `vector.similarity_function`: 'cosine'
}};
```

Querying it has **two syntaxes right now**:

| Approach | Versions | Status |
|---|---|---|
| `db.index.vector.queryNodes()` | 5.x+ | deprecated as of 2026.04, still works |
| Cypher 25 `SEARCH` clause | 2026.01+ | preferred, GA in 2026.02 |

```cypher
-- portable (works everywhere, deprecated but functional)
CALL db.index.vector.queryNodes('scene_embedding', 5, $queryVector)
YIELD node, score
MATCH (node)<-[:HAS_SCENE]-(v:Video)
RETURN v.title, node.title, node.start, score;
```

**Recommendation: use `queryNodes` on the day.** Deprecated ≠ removed, it works on every
version including old Docker images, and you will not be judged on Cypher modernity. Only
reach for `SEARCH` if you're on Aura (which runs latest) *and* want in-index filtering.

Also new: `ai.text.embed()` / `ai.text.embedBatch()` embed inside Cypher (2025.12+). Nice,
but irrelevant here — your embeddings come from Marengo, not from text.

Set vectors via `db.create.setNodeVectorProperty` in an `UNWIND` batch, not one-by-one.

### Getting an instance
- **Aura free** — no credit card, APOC preinstalled, always latest version. Fastest path.
- **Docker** — `NEO4J_PLUGINS` env var for APOC. Works offline; venue wifi is a real risk,
  so having this as a fallback is cheap insurance.

### Official MCP server
Exposes `get-schema`, `read-cypher`, `write-cypher`, `list-gds-procedures`. The `get-schema`
tool exists specifically because LLMs hallucinate labels and properties — worth wiring up if
your agent writes its own Cypher.

**[VERIFY]** Install method — the repo mentions a downloadable binary, PyPI has
`mcp-neo4j-cypher`, and one doc page said `pip install neo4j-mcp-server`. Three different
answers; confirm before depending on it. Env vars are consistently
`NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` / `NEO4J_DATABASE`.

---

## 3. Strands Agents

`pip install 'strands-agents[openai]' strands-agents-tools`

```python
from strands import Agent, tool
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    client_args={"api_key": "..."},
    model_id="gpt-4o",
    params={"max_tokens": 1000, "temperature": 0.7},
)

@tool
def query_graph(cypher: str) -> str:
    """Run a read-only Cypher query against the video context graph."""
    ...

agent = Agent(model=model, tools=[query_graph])
print(agent("Which people appear in more than one video?"))
```

- Tools are plain decorated functions — the docstring is the tool description the model sees.
  Write those docstrings carefully, they're your prompt surface.
- `agent.structured_output(PydanticModel)` for schema-constrained extraction.
- `agent.stream_async(prompt)` yields events with a `"data"` key — use for demo polish.
- Defaults to Bedrock if you don't pass a model. Pass `OpenAIModel` explicitly.
- Concepts beyond basics: hooks (intercept/validate), steering (feedback instead of hard
  blocks), conversation management (sliding window / summarization).

**[VERIFY]** Docs live at `strandsagents.com/docs/...` now; older `/latest/documentation/docs/`
and `/0.1.x/` paths still rank in search and are stale. The GitHub org's main repo is
`strands-agents/harness-sdk`, which is confusing — the pip package is `strands-agents`.

---

## 4. Proposed graph schema

```
(:Video   {id, title, duration, source_url, tl_asset_id, tl_index_id})
(:Scene   {id, start, end, title, summary, embedding})   ← 512-d vector here
(:Entity  {id, name, norm_name, type})                   ← person | object | org | place
(:Tag     {name})
(:Utterance   {text, start, end, speaker})
(:OnScreenText {text, start, end})

(:Video)-[:HAS_SCENE]->(:Scene)
(:Scene)-[:NEXT]->(:Scene)                        temporal chain
(:Scene)-[:FEATURES {confidence}]->(:Entity)
(:Scene)-[:TAGGED]->(:Tag)
(:Entity)-[:CO_OCCURS_WITH {count}]->(:Entity)    derived, computed after ingest
```

`NEXT` and `CO_OCCURS_WITH` are what make this a graph rather than a table with a vector
column. They're also cheap to compute and they're what lets you answer things a vector DB
structurally cannot: *"what happened right after X appeared?"*, *"who is only ever on screen
with Y?"*, *"shortest path between these two people across the whole corpus."* If the graph
only ever gets queried by similarity, a judge will fairly ask why it's a graph at all.

### The hard part: entity resolution

Analyze two videos independently and you get `"a man in a red jacket"` and `"the man in red"`
as two nodes. Cross-video queries then return nothing, and cross-video queries are the entire
point of a context graph.

Minimum viable fix — normalize and `MERGE`:

```cypher
MERGE (e:Entity {norm_name: toLower(trim($name))})
  ON CREATE SET e.id = randomUUID(), e.name = $name, e.type = $type
```

Better, if time allows: embed entity names and merge above a cosine threshold. This is the
single highest-leverage thing to get right, and the most common place these projects quietly
fail — the demo looks fine on one video and falls apart on three.

---

## 5. Risks specific to this event

| Risk | Mitigation |
|---|---|
| ~5h of real build time (11:00→16:00, minus lunch), not "a full day" | Pre-decide schema; don't design at the venue |
| Video indexing latency is unpredictable | Index 2–3 short clips early, cache the JSON to disk, develop against the cache |
| Two conflicting TwelveLabs call shapes in docs | Read the starter template first, then write |
| Blog tutorials use removed `/summarize` + Marengo 2.7 | Trust `docs.twelvelabs.io`, not blogs |
| Venue wifi | Docker Neo4j fallback; cached fixtures so you can demo offline |
| Solo, no API keys yet | Write against a thin interface, mock it, swap in real clients when keys land |

The schedule as posted lists "11:00 PM — Hacking Begins"; that's a typo for 11:00 AM.

---

## Sources

- [Strands Python quickstart](https://strandsagents.com/docs/user-guide/quickstart/python/) ·
  [OpenAI provider](https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/) ·
  [strandsagents.com](https://strandsagents.com/)
- [TwelveLabs Python SDK](https://github.com/twelvelabs-io/twelvelabs-python/blob/main/README.md) ·
  [release notes](https://docs.twelvelabs.io/docs/get-started/release-notes) ·
  [structured responses](https://docs.twelvelabs.io/docs/guides/analyze-videos/structured-responses) ·
  [Marengo 3.0](https://www.twelvelabs.io/blog/marengo-3-0)
- [Neo4j vector indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) ·
  [vector index skill](https://github.com/neo4j-contrib/neo4j-skills/blob/main/neo4j-vector-index-skill/README.md) ·
  [Neo4j MCP](https://github.com/neo4j/mcp) ·
  [vector search with filters](https://neo4j.com/blog/genai/vector-search-with-filters-in-neo4j-v2026-01-preview/)

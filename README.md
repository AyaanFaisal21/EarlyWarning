# Early Warning

**The incidents nobody reported.**

Near misses are supposed to be a leading indicator. They can't be, if nobody files them.

Safety cameras record every near-miss that happens. Almost none of them become a report.
This turns that footage into a graph, groups events by what actually caused them, and
surfaces the ones that are getting worse while the reports dry up.

---

## The problem

**90% of workplace incidents, hazards, and near misses go unreported.**
*(Benchmark Gensuite 2026 EHS Benchmarking Report; other studies put it at 50–90%.)*

Not because people are lazy. Because they don't recognise the event. Nothing happened — the
forklift stopped, the worker stepped back, the load swung past. There's nothing to file. A
better reporting form does not fix a recognition failure, which is why the instrument has to
be the camera.

Meanwhile employers pay **over $1 billion per week** in direct workers' compensation for
disabling non-fatal injuries. *(Liberty Mutual 2025 Workplace Safety Index — $58.78B/year;
note the 2025 index reflects 2022 data.)*

### Why "just count near-misses" already failed

The obvious response — count near-misses, drive the number down — was tried for ninety
years, and it does not work. **Minor injuries have declined for decades while fatalities and
serious injuries have not fallen at the same rate.** Frequency and severity are different
problems with different causes.

So the field moved to **SIF potential**: instead of counting events, judge which ones *could*
have killed someone if conditions had been slightly different.

**That reframing is the technical opportunity.** Judging SIF potential means looking at a
scene and asking a counterfactual — how close was it, what control was missing, what would
have had to change. That is a visual, structural, relational judgement. It is not a count,
which is exactly why it is still a human job, and exactly what a vision model plus a graph
can do.

---

## What it does

Four things, in order of how convincing they are:

1. **Finds the reporting gap** — patterns the cameras saw repeatedly that produced no report.
2. **Ranks by unseen risk** — accumulated SIF potential × the fraction that stayed invisible.
   Dangerous *and* unknown outranks both dangerous-but-tracked and frequent-but-harmless.
3. **Detects normalization of deviance** — patterns where occurrences rise, the safety margin
   shrinks, and the report rate falls. An organisation isn't getting safer there; it's
   getting desensitised.
4. **Names the control to fix** — which single absent control spans the most high-potential
   events, across the most distinct patterns.

---

## Why this needs a graph, specifically

Every query in [queries.cypher](queries.cypher) is a set operation, an absence test, or a
multi-hop traversal. None is expressible as similarity search:

| Question | Operation | Vector DB |
|---|---|---|
| Which patterns produced no report? | negation over a relationship | cannot express absence |
| Which control spans the most patterns? | two-hop traversal + distinct count | no traversal |
| Is the margin shrinking while reports fall? | windowed aggregation over time | no aggregation |
| Which is riskiest given severity *and* invisibility? | weighted set arithmetic | no set ops |

The nearest-neighbour answer to "what is missing" is silently wrong — it returns the closest
thing that *does* exist.

**And the grouping key is a subgraph, not a point in embedding space.** Two events are the
same pattern when they share causal structure: hazard type, absent controls, actor types.
Embedding similarity would group by *appearance* — two unrelated failures in the same aisle
collapse together, while the same root cause at a second site never does. See
`fingerprint()` in [src/loader.py](src/loader.py).

Embeddings still earn their place, at one specific job the graph can't do: given an event
somebody *did* report, find the ones nobody reported that look like it (Q5).

---

## Stack

| | Role | Why it's load-bearing |
|---|---|---|
| **TwelveLabs** | Pegasus extracts counterfactual, timestamped events under a strict JSON schema; Marengo 3.0 gives 512-d embeddings | The signal is entirely visual — proximity, guarding, sightlines. No transcript exists |
| **Neo4j** | Pattern fingerprinting, absence queries, temporal drift, control leverage | The grouping key and every headline query are relational |
| **OpenAI** | Reads a pattern's whole subgraph and writes its name, root-cause hypothesis, and the action to take | Its input is aggregated relational structure that only exists after the graph is built |
| **Strands** | Orchestrates ingest → extract → resolve → cluster → answer | Graph exposed as agent tools |

### The extraction schema is the core IP

[src/extraction.py](src/extraction.py) constrains every taxonomy field to an `enum`. This is
deliberate: free-text extraction yields "forklift near pedestrian" and "pedestrian close to a
forklift" as different things, which destroys cross-video grouping. Enum constraints turn
open generation into classification — fingerprints become exact-match, entity resolution
disappears, and clustering is a `MERGE` rather than a threshold you tune under time pressure.

We also deliberately **do not ask the model for distances in metres.** Monocular video does
not support that and a float invites confident fabrication. Proximity is banded
(`contact / under_1m / 1_to_3m / over_3m`), which is what a human reviewer actually judges,
and bands are sufficient to detect drift.

### What OpenAI is actually given

[src/context.py](src/context.py) serialises a pattern's entire subgraph — severity
distribution across dozens of clips, proximity and reporting trends over time, which other
patterns share an absent control, and the counterfactuals the extractor produced. That
payload cannot be assembled from raw footage, from a vector index, or from any single
video; it exists only after the graph does. So the model is reasoning over the graph, not
performing another pass of extraction.

Inspect exactly what would be sent, without spending a token:

```bash
python src/brief.py          # prints the assembled prompts
```

Three rules are enforced in the system prompt because they are the failure modes that would
make the output worse than nothing: ground every claim in the supplied data; **never blame a
worker, name the missing control** (blame is why 90% of near misses go unreported — a tool
that reproduces it makes the problem worse); and say when the evidence is thin.
`src/selfcheck.py` asserts all three are still in the prompt.

---

## Run it

Works with **no API keys**. The graph half is entirely real; extraction falls back to
ground-truth simulation so the full pipeline is exercisable today.

```bash
python -m venv .venv && source .venv/bin/activate   # see pre-flight note below
pip install -r requirements.txt
docker compose up -d
docker exec -i earlywarning-neo4j cypher-shell -u neo4j -p hackathon2026 < schema.cypher

python src/selfcheck.py            # taxonomy/schema/fingerprint consistency, no DB needed
python src/ingest.py --reset       # synthetic corpus
python src/demo.py                 # the four beats  (--pause to step through)
```

Against the real clips (40 already in `data/`, see [SOURCES.md](SOURCES.md)):

```bash
python src/fetch_footage.py --per-class 5     # if data/ is empty
python src/ingest.py --reset --videos data/*.mp4
python src/score.py                           # extraction accuracy vs ground truth
```

With keys, the same commands go live — plus:

```bash
export TL_API_KEY=... TL_INDEX_ID=... OPENAI_API_KEY=...
python src/agent.py "what should the safety committee look at this month?"
```

Neo4j browser: <http://localhost:7474> (neo4j / hackathon2026), then anything from
[queries.cypher](queries.cypher).

### Pre-flight notes (verified, not guessed)

- **Use a virtualenv.** Installing `strands-agents[openai]` upgrades `starlette`, which
  breaks a pre-existing `fastapi` in a shared environment.
- **macOS python.org builds** ship without the system trust store, so `urllib` fails cert
  verification where `curl` succeeds. `src/fetch_footage.py` handles it via `certifi`.
- **Beat 3 belongs to the synthetic corpus.** The Mendeley clips carry no per-clip
  timestamp, so `occurred_at` is *assigned* when ingesting real footage. Drift results over
  real clips are not a temporal finding and must not be presented as one.

### Verified output

```
loaded 109 events, 43 reports
  could have killed someone:  54 events,  6% reported
  minor potential:            55 events, 73% reported
```

That inversion is the entire thesis: **reporting collapses exactly where severity climbs.**

---

## The pitch site

`EWLandingPage/` is a Next.js app that walks the whole argument: hero over a 3D grid, the
underreporting numbers, the near-miss / incident / accident ladder, the four-step pipeline
with a per-step "why this tool", a demo slot, and the automation closer.

```bash
cd EWLandingPage && npm install && npm run dev
```

Everything is driven off one normalised scroll value in `lib/useScrollProgress.ts`, so the
camera dolly, the copy fades, and the section reveals stay in lockstep. Timeline:

| Scroll | Section |
|---|---|
| 0.00 – 0.18 | camera descends into the grid, lines darken to black |
| 0.24 – 0.35 | the three statistics |
| 0.37 – 0.50 | accident → incident → near miss, revealed in reverse |
| 0.52 – 0.83 | pipeline: terminal centred, squeezing into a sidebar |
| 0.82 – 0.92 | demo video slot |
| 0.92 – 1.00 | why this gets harder |

Drop a recording at `EWLandingPage/public/demo.mp4` and the demo section plays it.

### Deploying to Vercel

Import the repo and **set the root directory to `EWLandingPage`** — the Next.js app is not
at the repo root. Framework preset auto-detects; no environment variables are needed, since
the site is static and talks to nothing.

⚠️ **New files need a dev-server restart.** Next's fast refresh repeatedly served stale
bundles during development — a component would compile cleanly and simply not render. If a
change appears not to have applied, `rm -rf EWLandingPage/.next` and restart before
assuming it is broken.

---

## Honest limitations

- **The corpus in `src/seed.py` is synthetic** and deliberately constructed to contain a
  drift signal, so the queries can be verified against known ground truth rather than
  eyeballed. It is not evidence the extraction works on real footage.
- **No public corpus of workplace near-miss footage exists** — the footage that matters is
  the footage nobody publishes. Real validation needs proxy footage (warehouse/forklift) or
  a partner site.
- **SIF potential is a model judgement**, not a measurement. It should rank a review queue,
  never gate a decision on its own.
- **The unit of analysis is the hazard, never the individual.** No person identification, no
  re-identification, no worker-level metrics. This is a hazard-finding tool and it should
  stay one.
- `db.index.vector.queryNodes` is deprecated as of Neo4j 2026.04 but works on every version
  including older Docker images. On 2026.01+ the `SEARCH` clause is preferred.

---

## Files

| | |
|---|---|
| [src/taxonomy.py](src/taxonomy.py) | Controlled vocabularies — the enums everything keys on |
| [src/extraction.py](src/extraction.py) | TwelveLabs: SIF-potential JSON schema, upload, embed |
| [src/loader.py](src/loader.py) | Neo4j loading + `fingerprint()` |
| [src/groundtruth.py](src/groundtruth.py) | Dataset labels → taxonomy; extraction simulation |
| [src/seed.py](src/seed.py) | Synthetic corpus with a known drift signal |
| [src/ingest.py](src/ingest.py) | End-to-end pipeline (synthetic or real clips) |
| [src/fetch_footage.py](src/fetch_footage.py) | Stratified pull of real CCTV from Mendeley |
| [src/score.py](src/score.py) | Extraction accuracy vs ground truth |
| [src/context.py](src/context.py) | Subgraph → prompt payload; inspectable without a key |
| [src/brief.py](src/brief.py) | OpenAI layer: pattern naming, root cause, recommended action |
| [src/demo.py](src/demo.py) | The four beats, one command |
| [src/selfcheck.py](src/selfcheck.py) | Consistency checks — no DB or key needed |
| [src/agent.py](src/agent.py) | Strands agent over the graph |
| [schema.cypher](schema.cypher) | Constraints, indexes, 512-d vector index |
| [queries.cypher](queries.cypher) | The five demo queries |
| [DEMO.md](DEMO.md) | Run sheet |
| [src/fetch_nvidia.py](src/fetch_nvidia.py) | Pull synchronised camera views of one near-miss run |
| [EWLandingPage/](EWLandingPage) | The pitch site — Next.js, scroll-driven |
| [SOURCES.md](SOURCES.md) | Footage sources, licences, what was rejected |
| [SAFETY_EVIDENCE.md](SAFETY_EVIDENCE.md) | Every statistic, with what's citable and what isn't |

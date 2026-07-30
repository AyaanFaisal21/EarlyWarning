# Early Warning — demo script

Structured against the three judging criteria. ~2:30 spoken.
Scroll cues in brackets. Files to open in **§3**.

---

# 1 · THE PROBLEM

**[hero — don't scroll yet]**

> How much is a human life worth?

*Pause. Don't answer it.*

> Bit of a hard question. But American employers answer it every week — they pay out over
> **a billion dollars a week** in workers' compensation, for injuries that have already
> happened.
>
> In 2024 alone, **five thousand and seventy** people went to work and didn't come home.

**[scroll: numbers]**

> The National Safety Council says three quarters of workplace accidents were preceded by a
> near miss. A warning. And **ninety percent of those warnings are never reported** —
> because to the person it happened to, nothing really happened.

**[scroll: cards]**

> That's what a near miss is. An event where nobody gets hurt, but one that often comes
> before an accident.
>
> And it's getting worse. Pedestrians struck by workplace vehicles are up **nineteen
> percent**. If you almost get hit, you're thankful, you go about your day — and you wonder
> who you'd even report it to.
>
> Meanwhile autonomous machinery is arriving on those same floors, causing the same near
> misses, reporting none of them — leaving only footage.

**[scroll: the problem, and what it costs]**

> That's right. Footage is everywhere. Nobody can watch it, and nobody knows what to look
> for. **Early Warning watches.**

---

# 2 · THE TECH STACK

*Say the enabling claim, not just the name. This is the criterion they're scoring.*

**[scroll: pipeline]**

> Four technologies, and each one does something the others structurally cannot.

**[step 01]**

> **TwelveLabs.** The signal here is entirely visual — proximity, guarding, whether someone
> crossed a walkway. There is no transcript. A speech model reads nothing.
> **Without it there is no input at all.**

**[step 02]**

> Real CCTV on the left, a rendered simulation on the right. They look nothing alike and
> produce the **same fingerprint**, because we hash what the extractor found, not what the
> frame looked like.
>
> We tried embeddings first. They failed — everything sat at 0.98 similarity.
> **Structure worked where appearance couldn't.**

**[step 03]**

> **Neo4j.** Every question here is about what's *absent* — which patterns produced no
> report. Ask a vector database and it hands you the nearest thing that exists.
> **Only a graph can count what isn't there.**

**[step 04]**

> **OpenAI** reads the assembled subgraph — never a video frame — and writes a brief with a
> named cause and one action. **Without the graph there'd be nothing to reason over.**
>
> And **Strands** runs two agents: one enforcing that structured output, one with the graph
> exposed as tools. **That's what lets it write its own Cypher.**

---

# 3 · LIVE DEMO + CODE

## The live bit — ask the graph a question

```bash
python src/agent.py "Which hazard patterns produced no report at all?"
```

> Nobody wrote this query. It reads the real schema first, composes the Cypher, and runs it.

**Expected answer:** 46 unreported patterns; biggest is *forklift — vehicle pedestrian
proximity, no segregated walkway*, fingerprint `5649abdb63e19bdf`, **17 events**.

⚠️ Takes ~20s. If the room is tight, show the saved output instead and say so.

## Four files, in this order

| # | File | What to say |
|---|---|---|
| 1 | **`src/extraction.py`** — `EVENT_SCHEMA` | "Every field is an enum. Free text here and 'forklift near pedestrian' and 'pedestrian close to a forklift' become different things — cross-video grouping dies at the first clip." |
| 2 | **`src/loader.py`** — `fingerprint()` | "Twelve lines, no vendor. Hash the hazard, the absent controls, the actors. That's why a real clip and a simulation collapse to one pattern." |
| 3 | **`queries.cypher`** — the reporting gap | "`NOT (e)-[:GENERATED]->(:Report)` — a negation over a relationship. This is the query a vector database cannot express." |
| 4 | **`src/agent.py`** — the tools | "`get_graph_schema` exists because models invent labels. It reads what's actually there before writing anything." |

*If you only get one: **`fingerprint()`**. Twelve lines carrying the whole argument.*

---

# CLOSE

**[scroll: future]**

> We can't make people report near misses. We've tried for ninety years.
>
> So stop trying. Let **Early Warning** be the infrastructure that does it for them — now,
> and when the machines arrive.

---

## If you're long

Cut step 02's embeddings sentence and the fourth file. Keeps all three criteria covered.

---

## If asked

**"How accurate is it?"**
High recall on hazard presence. Against a labelled CCTV set we got ~51% precision — but
those labels encode *human compliance*, whether a worker stayed inside a painted line, which
is a different question from whether a machine did something unexpected. We don't claim
compliance classification. It ranks a review queue; a human closes the loop.

**"Where's AWS?"**
The graph runs on Neo4j Aura, hosted on EC2 in us-east-1. Strands is AWS's agent SDK and
runs two agents here. Bedrock is validated and wired next — we ran out of clock.

**"Isn't this surveillance?"**
The unit of analysis is the hazard, never the person. No identification, no worker-level
metrics. The output names a missing barrier.

**"Is the data real?"**
Both. Real factory CCTV under CC BY, plus NVIDIA's openly licensed simulation set. What
you're seeing is a completed pipeline run over 79 clips.

**"All accidents start as near misses, right?"**
Careful — that's Heinrich's pyramid, and it's discredited. Minor injuries fell for decades
while fatalities didn't. That's why the field moved to SIF potential, and why we rank by
what could have killed someone rather than by count.

**"Who acts on it?"**
EHS manager → safety committee → maintenance installs the control. Then the loop closes: we
keep counting, so if the pattern drops you know the fix worked. No manual programme can tell
you that, because the events were never counted to begin with.

---

## Numbers, with sources

| Claim | Source |
|---|---|
| >$1B/week direct workers' comp | Liberty Mutual Workplace Safety Index 2025 |
| 5,070 fatal work injuries, 2024 | BLS Census of Fatal Occupational Injuries |
| Pedestrians struck by vehicles +19% | BLS, same |
| 90% of near misses unreported | Benchmark Gensuite 2026 EHS Benchmarking Report |
| 75% of accidents preceded by a near miss | National Safety Council |

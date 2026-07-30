# Near-miss evidence — what's citable, what isn't

Reference for the reporting-gap pitch. **Read the "don't cite" section before using any of
this on stage** — the obvious version of this pitch is built on a discredited model, and a
judge who works in EHS will know.

---

## 1. The reporting gap (solid, cite freely)

- **90% of workplace incidents, hazards, and near misses are underreported** — Benchmark
  Gensuite 2026 EHS Benchmarking Report.
- Other studies put it at **50–90%**. Use the range if you want to be conservative.
- **Why** people don't report: they don't recognize the event as a near-miss, they fear
  blame, or there's no easy channel. Paper forms and slow portals actively discourage it.

That last point matters for positioning: the gap is not laziness, it's **recognition
failure**. People don't file reports for things they didn't notice were events. You can't
fix that with a better form — which is precisely why cameras are the right instrument.

---

## 2. The money (solid, but know the caveats)

**Liberty Mutual 2025 Workplace Safety Index:**
- **$58.78B/year** — direct US employer cost of serious nonfatal workplace injuries
- **$50.87B** — top 10 causes, i.e. 86% of that total
- **Over $1 billion *per week*** in direct workers' comp for disabling nonfatal injuries
- Overexertion (outside sources): **$13.7B**; falls on same level: **$10.5B**
- 56% of injuries involve back/shoulder/knee/multiple body parts → **$32.6B**

⚠️ **The 2025 index reflects 2022 data** — a three-year lag. Say "most recent index" not
"in 2025," or someone will correct you.

**National Safety Council:** workplace injuries and deaths cost the US economy
**$176.5B in 2023.**

⚠️ These two figures measure **different things** and must not be conflated. Liberty Mutual
is direct employer cost of *serious nonfatal* injuries. NSC is *total economic* cost
including fatalities and indirect costs (lost productivity, admin, business disruption).
Quoting them as if they're comparable is the fastest way to look sloppy.

**Best single line:** *"Employers pay more than a billion dollars a week in direct workers'
comp for injuries that didn't have to happen."*

---

## 3. ⛔ Do NOT cite Heinrich's pyramid as fact

The tempting version of this pitch is "Heinrich showed 300 near misses precede every major
injury, so count near misses." **That pitch is wrong, and it's the tell of someone who
googled the topic for an hour.**

The models, for reference:
- **Heinrich (1931)** — 300 near misses : 29 minor injuries : 1 major. From ~75,000 industrial
  incident reports reviewed for the insurer Travelers.
- **Bird (1966)** — 600 near misses : 30 property-damage : 10 minor : 1 serious. From 1.7M
  accident reports across ~300 companies.

Why it's discredited:
- Research finds the pyramid **statistically invalid** as a predictive model.
- **The killer empirical fact: minor injuries have declined over decades while fatalities and
  serious injuries have not declined at the same rate.** That directly falsifies the core
  claim — that driving down frequency drives down severity.
- It's criticized as over-simplistic for complex work environments, and for placing
  responsibility almost entirely on worker behavior.
- The common misuse — "reduce frequency and severity follows" — leads to bad resource
  allocation.

**If you mention it at all, mention it as the thing that failed.**

---

## 4. ✅ The argument that actually works — SIF potential

Here's the move: **the reason Heinrich failed is the reason your product exists.**

The pyramid assumed near misses are fungible — that they can be counted. They aren't. Modern
EHS practice replaced counting with **SIF potential (pSIF)** — Serious Injury or Fatality
potential:

> Serious harm is driven by **specific exposures and weak controls, not injury frequency**.
> Near misses don't necessarily mean a fatality is around the corner. The focus must be on
> the subset of near misses **with SIF potential** — situations that could have caused major
> harm if conditions, systems, or acts had been slightly different. The contributing factors
> behind SIFs are *different* from those behind non-SIFs.

Now read that as a technical spec. Assessing SIF potential requires asking **"what would have
happened if conditions had been slightly different?"** That is:

- **Visual** — you have to see the scene: proximity, load, footing, sightlines, guarding.
- **Counterfactual and structural** — about the *configuration* of hazards, not a tally.
- **Relational** — which conditions co-occurred, and which controls were absent.

None of that is a count. All of it is a VLM plus a graph. **This is the strongest technical
argument available in the whole project**, and it's honest:

> "The industry already knows counting near misses doesn't work — that's why they moved to
> SIF potential. But judging potential means looking at the scene and asking what would have
> happened if things had been slightly different. That's why it's still a human job. It's
> also exactly what a vision model plus a graph can do."

---

## 5. The "near miss became a real incident" evidence you asked about

**Aggregate statistical evidence: weak and contested. Don't overclaim it.**

- A PubMed study found the relationship between near-miss occurrence and future
  medically-attended injuries **appeared weak**, with numbers too small to determine whether
  specific mechanisms predict same-type injuries.
- An IJSRP study reports an inverse correlation between near-miss reporting frequency and
  major incident rates. ⚠️ **Heavily confounded** — organizations that report more near misses
  also tend to have better safety culture across the board. Reporting rate is a proxy for
  culture, not a cause of safety. Don't present this as causal.

**Case-study evidence: overwhelming. This is where your pitch gets its teeth.**

### BP Texas City — the number you want

March 23, 2005: explosions during an isomerization unit startup killed **15 workers and
injured 170**.

The precursor chain is documented:
- Internal BP documents from **2002–2005** showed awareness of significant safety problems at
  Texas City **and 34 other BP business units worldwide**.
- **March 2004** — a blast and fire at the same refinery forced an evacuation. OSHA fined it
  **$63,000**.
- **One year later**, 15 people were dead.
- OSHA subsequently found **300+ willful violations** and fined BP **$21.3 million**, the
  largest in OSHA history at the time. BP committed roughly **$1 billion over five years** to
  the site.
- CSB found budget cuts had progressively degraded safety — fixed costs cut 25% from
  1998–2000.

**The ratio is the pitch:** a **$63,000** precursor, ignored, became **15 deaths, a $21.3M
fine, and a $1B remediation.** That is the "near miss that became real" statistic, and it's
better than any correlation coefficient.

### Normalization of deviance — the name for what you described

You asked about "events that don't get a name because they only nearly caused a problem."
Sociologist **Diane Vaughan** named it while analyzing Challenger: **normalization of
deviance** — "the process in which deviance from correct or proper behavior or rule becomes
culturally normalized."

Vaughan's mechanism, which is the whole thesis of your product:

> People become **so insensitive to deviant practice that it no longer feels wrong**.
> Insensitivity occurs insidiously, sometimes over years, because disaster doesn't happen
> until other critical factors line up. There is "a long incubation period with early warning
> signs that were either misinterpreted, ignored or missed completely."

Concretely: O-ring erosion and blow-by were **accepted as risks** before Challenger. Foam
strikes to the orbiter were **accepted as risks** before Columbia. Each individual event
looked survivable, because each individual event *was* survivable — until one wasn't.

**And here is the connection that makes this a software problem:**

> Normalization of deviance is a **memory failure**. Deviance normalizes because nobody is
> comparing today's event against the forty similar events from the last two years. Each one,
> viewed alone, looks fine. Only the aggregate shows the drift. No human holds that. A graph
> does.

That's your closing line. It reframes the product from "video analytics" to "institutional
memory," which is a much bigger and more defensible claim — and it's the thing a graph is
uniquely good at.

---

## 6. Suggested pitch order

1. **90% of near misses go unreported** — and not from laziness; people don't file reports
   for things they didn't notice were events.
2. **Over $1B/week** in direct workers' comp. The money is real.
3. **Don't say Heinrich.** Say: the industry tried counting near misses and it failed —
   minor injuries fell, fatalities didn't.
4. **So the field moved to SIF potential**: which near misses *could* have killed someone.
   That's a judgment about the scene, not a count — which is why it's still human work.
5. **BP Texas City**: $63,000 fine in 2004 → 15 dead, $21.3M, $1B in 2005.
6. **Close on Vaughan**: normalization of deviance is a memory failure, and memory is what a
   graph is for.

Steps 3 and 4 are what separate this from every other "AI for safety" pitch. Most teams will
cite the pyramid. Being the team that knows *why the pyramid is wrong* is worth more than any
other 20 seconds you have.

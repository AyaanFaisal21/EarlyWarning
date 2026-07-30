'use client'

import { GraphSchema } from '@/components/GraphSchema'
import { HazardFrame } from '@/components/HazardFrame'
import { BANDS, band } from '@/lib/timeline'
import { remap } from '@/lib/useScrollProgress'

/**
 * The pipeline, in three scroll phases:
 *
 *   1. a terminal listing every step, centred
 *   2. that terminal squeezing left into a sidebar while the detail panel opens
 *   3. the sidebar tracking which step you are reading, marked in caution tape
 *
 * One component owns all three because they share the same step list and the same active
 * index. Splitting them would mean duplicating that state and keeping two sources of truth
 * in sync for no gain.
 */

const [PIPELINE_AT, PIPELINE_END] = BANDS.pipeline
const SQUEEZE_FROM = PIPELINE_AT + 0.03
const SQUEEZE_TO = PIPELINE_AT + 0.07
// Divide the remaining scroll evenly so the last step always finishes before the section
// starts fading, however the band is later retuned.
const STEP_SPAN = (PIPELINE_END - 0.04 - SQUEEZE_TO) / 4

type Step = {
  id: string
  label: string
  tool: string
  aws?: boolean
  call: string
  handoff: string
  /** Why this tool and not something simpler. The question a judge asks first. */
  why: string
  /**
   * The card that slides over the description partway through each step.
   *
   * `code` is verbatim from the repo — a paraphrased snippet is a liability if anyone
   * reads it closely. `images` is the slot for stills and graph renders; when present the
   * card shows those instead.
   */
  code: { lang: string; body: string }
  /** Real footage. Shown instead of code when present. */
  video?: { src: string; caption: string }
  /** Two clips that resolve to the same fingerprint. */
  pair?: { left: { src: string; label: string }; right: { src: string; label: string }; fingerprint: string; caption: string }
  /** The schema diagram, drawn in-palette rather than screenshotted. */
  graphic?: 'schema'
  detail: string[]
}

const STEPS: Step[] = [
  {
    id: 'watch',
    video: {
      src: '/clips/forklift-nearmiss.mp4',
      caption:
        'Extracted from this clip: vehicle_pedestrian_proximity · sif fatal · proximity under_1m — "a pedestrian worker stands in the path of a reversing forklift".',
    },
    code: { lang: 'python', body: `result = client.analyze(
    model_name="pegasus1.5",
    video=VideoContext_AssetId(asset_id=asset_id),
    prompt_v_2=AnalyzePromptV2(input_text=PROMPT),
    response_format=SyncResponseFormat(
        type="json_schema",
        json_schema=EVENT_SCHEMA,   # every field enum-constrained
    ),
)
return json.loads(result.data)["events"]` },
    label: 'WATCH',
    tool: 'TwelveLabs · Pegasus 1.5',
    call: 'analyze(video, response_format=json_schema)',
    handoff: 'pixels → rows',
    why: 'Because the signal is entirely visual. Proximity, guarding, sightlines, whether a walkway was crossed — none of it is spoken, so there is no transcript to fall back on. A speech model reads nothing here. This needs a model that watches.',
    detail: [
      'Upload is two steps that return two different IDs — asset, then indexed asset. analyze() and embed() key off the asset ID; passing the other returns 404 and reads like a failed upload.',
      'Every taxonomy field is enum-constrained. Free text here yields "forklift near pedestrian" and "pedestrian close to a forklift" as different things, and cross-video grouping dies at the first clip.',
      'The schema asks what nearly happened, not what happened. A required counterfactual field forces the model to name the change that would have caused injury.',
      'Measured honestly: high recall on hazard presence, unreliable at compliance classification. Roughly 25s to upload and index, 8s to analyze.',
    ],
  },
  {
    id: 'structure',
    pair: {
      left:  { src: '/clips/real-cctv.mp4',    label: 'real CCTV · Turkish factory' },
      right: { src: '/clips/sim-nearmiss.mp4', label: 'simulation · NVIDIA PhysicalAI' },
      fingerprint: '5649abdb63e19bdf',
      caption:
        'Left: a real factory — a forklift swinging round with a load while someone walks past. Right: a rendered simulation on another continent. Both extracted to the same hazard and the same three absent controls, so both hash to the same pattern. The simulation set is the counterfactual made visible: our extractor writes what would have had to change for someone to be hurt, and these runs show that configuration playing out with less margin left. Embeddings could not bridge these two — within a corpus events sit at 0.98 similarity, across corpora 0.88. The fingerprint does, because it hashes what the extractor found rather than what the frame looked like.',
    },
    code: { lang: 'python', body: `def fingerprint(event) -> str:
    """The grouping key: a subgraph signature, not a
    point in embedding space."""
    parts = [
        event["hazard_type"],
        ",".join(sorted(event["missing_controls"])),
        ",".join(sorted(event["actors"])),
    ]
    return sha1("|".join(parts).encode()).hexdigest()[:16]` },
    label: 'STRUCTURE',
    tool: 'no vendor — 12 lines',
    call: 'sha1(hazard | sorted(controls) | sorted(actors))',
    handoff: 'an event → an instance',
    why: 'Because grouping by appearance is the wrong grouping. Two events belong together when they share a cause, not when their pixels match — and once extraction speaks a closed vocabulary, that shared cause is a string you can hash. No model required.',
    detail: [
      'Two events are the same pattern when they share causal structure: hazard type, absent controls, actor types. Not when their pixels look alike.',
      'Embedding similarity would group by appearance — two unrelated failures in one aisle collapse together, while the same root cause at a second site never does.',
      'Because extraction is enum-constrained, the key is exact-match. No similarity threshold to tune under time pressure, and no entity resolution step at all.',
      'All 720 hazard × actor × control combinations were checked: zero collisions.',
    ],
  },
  {
    id: 'connect',
    graphic: 'schema',
    code: { lang: 'cypher', body: `// the reporting gap — a negation over a relationship
MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH p, count(e) AS seen, count(r) AS filed
WHERE filed = 0 AND seen >= 3
RETURN p.title AS pattern, seen
ORDER BY seen DESC` },
    label: 'CONNECT',
    tool: 'Neo4j · Aura',
    call: 'MERGE (p:Pattern {fingerprint}) ← INSTANCE_OF',
    handoff: 'rows → structure',
    why: 'Because every question worth asking here is about what is ABSENT. Which patterns produced no report. Which control is missing across the most events. Which conditions appear in failures and never in clean runs. Absence, negation and exhaustive counting are set operations — a graph does them natively, and a vector index cannot express them at all. Ask similarity search what is missing and it returns the nearest thing that exists.',
    detail: [
      'MISSING_CONTROL is a first-class edge, so "what was not there" is queryable rather than buried in a text field.',
      'GENERATED is defined by its absence. The reporting gap is NOT (e)-[:GENERATED]->(:Report) — a negation over a relationship.',
      'Three findings fall out: patterns that never produced a report, patterns whose proximity is shrinking while reporting falls, and the single absent control spanning the most high-potential events.',
      'None of these is similarity search. Ask a vector index what is missing and it returns the nearest thing that exists — silently wrong.',
    ],
  },
  {
    id: 'explain',
    code: { lang: 'python', body: `class PatternBrief(BaseModel):
    title: str
    root_cause_hypothesis: str
    why_unreported: str
    recommended_action: str
    confidence: Literal["low", "medium", "high"]

# input is a serialized subgraph, never a video frame
payload = render(pattern_context(graph, fingerprint))
brief = ask(agent, payload, PatternBrief)` },
    label: 'EXPLAIN',
    tool: 'OpenAI gpt-5.5 · Strands',
    aws: true,
    call: 'agent(payload, structured_output_model=PatternBrief)',
    handoff: 'findings → a brief',
    why: 'Because a ranked table is not a decision. The model reads aggregate structure that exists only after the graph is built — trends, distributions, shared controls across patterns — and turns it into a named cause and one action somebody can verify by Friday.',
    detail: [
      'The model reads a serialized subgraph: severity distribution across dozens of clips, proximity and reporting trends, and which other patterns share an absent control.',
      'That payload cannot be assembled from raw footage or from any single video. It exists only after the graph does — so this is reasoning over the graph, not another pass of extraction.',
      'Three rules are enforced and asserted by tests: ground every claim in the data, never blame a worker (blame is why near misses go unreported), and say when the evidence is thin.',
      'Output is a Pydantic-validated brief: title, root cause, why it was never filed, and one action verifiable this week.',
    ],
  },
]

/**
 * Where we are in the step sequence, as a continuous value.
 *
 * `index` is which step to show; `phase` is how far through it we are, 0 to 1. Rendering
 * straight off Math.floor makes the panel swap instantly at each boundary, which reads as a
 * glitch rather than a transition. Keeping the fractional part lets the panel dissolve out
 * and back in across the seam.
 */
function stepPosition(progress: number) {
  const raw = (progress - SQUEEZE_TO) / STEP_SPAN
  const clamped = Math.min(STEPS.length - 1e-4, Math.max(0, raw))
  const index = Math.floor(clamped)
  return { index, phase: clamped - index }
}

/** Trapezoid: fades in over the first slice of a step, out over the last. */
function crossfade(phase: number, ramp = 0.18) {
  return Math.max(0, Math.min(1, phase / ramp, (1 - phase) / ramp))
}

// Each step is two beats. Read the argument first, then the card carrying the evidence
// slides up over it. Splitting them this way means neither competes with the other for
// attention — a code block sitting beside prose gets skimmed past.
const CARD_IN = 0.42
const CARD_FULL = 0.62

export function PipelineSection({ progress }: { progress: number }) {
  // Hands the stage to the demo once the last step has had its turn.
  const sectionOpacity = band(progress, 'pipeline')
  const squeeze = remap(progress, SQUEEZE_FROM, SQUEEZE_TO, 0, 1)
  const { index: active, phase } = stepPosition(progress)
  const panel = crossfade(phase)
  const card = remap(phase, CARD_IN, CARD_FULL, 0, 1)
  const step = STEPS[active]

  // Terminal is the whole stage at first, then yields to the detail panel.
  const terminalWidth = 640 - squeeze * 330

  return (
    <div
      className="flex items-center justify-center px-6"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 14,
        opacity: sectionOpacity,
        pointerEvents: sectionOpacity < 0.1 ? 'none' : 'auto',
      }}
    >
      {/*
        justify-center is what makes the terminal start centred and slide left on its own.
        The detail panel has flex:0 until the squeeze begins, so at rest the terminal is the
        only thing in the row and centring puts it mid-screen. As the panel grows, the pair
        fills the row and the terminal is carried to the left edge — no position animation
        needed, and nothing to keep in sync.
      */}
      <div
        className="mx-auto flex w-full items-center justify-center"
        style={{ maxWidth: 1180, gap: 48 * squeeze }}
      >
        {/* ------------------------------------------------ terminal / sidebar */}
        <div style={{ width: terminalWidth, flexShrink: 0 }}>
          <div
            style={{
              background: '#0d0d0d',
              border: '1px solid rgba(255,255,255,.14)',
              borderRadius: 12,
              overflow: 'hidden',
              fontFamily:
                'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            }}
          >
            <div
              className="flex items-center gap-2 px-4 py-3"
              style={{ borderBottom: '1px solid rgba(255,255,255,.1)' }}
            >
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="ml-2 text-[11px] text-white/40">
                early-warning — pipeline
              </span>
            </div>

            <div className="px-4 py-4">
              {STEPS.map((step, i) => {
                const isActive = squeeze > 0.5 && i === active && phase > 0.06
                const row = (
                  <div
                    style={{
                      background: '#0d0d0d',
                      padding: squeeze > 0.5 ? '10px 12px' : '12px 14px',
                    }}
                  >
                    <div className="flex items-baseline gap-3">
                      <span
                        className="text-[11px]"
                        style={{ color: 'rgba(255,255,255,.3)' }}
                      >
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span
                        className="text-sm font-bold tracking-wide"
                        style={{ color: isActive ? '#f2c200' : '#ffffff' }}
                      >
                        {step.label}
                      </span>
                      <span className="text-[11px] text-white/35">{step.tool}</span>
                    </div>

                    {/* the call and the handoff drop away once we are in sidebar mode */}
                    <div
                      style={{
                        maxHeight: (1 - squeeze) * 60,
                        opacity: 1 - squeeze,
                        overflow: 'hidden',
                      }}
                    >
                      <div className="mt-2 text-[11px] leading-relaxed text-white/55">
                        {step.call}
                      </div>
                      <div className="mt-1 text-[11px] text-white/30">
                        {step.handoff}
                      </div>
                    </div>
                  </div>
                )

                return (
                  <div key={step.id}>
                    {isActive ? (
                      <HazardFrame thickness={3} radius={10} stripe={8}>
                        {row}
                      </HazardFrame>
                    ) : (
                      <div
                        style={{
                          border: '1px solid transparent',
                          borderRadius: 10,
                          overflow: 'hidden',
                        }}
                      >
                        {row}
                      </div>
                    )}

                    {i < STEPS.length - 1 && (
                      <div
                        className="py-1 pl-6 text-[13px]"
                        style={{ color: 'rgba(255,255,255,.25)' }}
                      >
                        │<br />▼
                      </div>
                    )}
                  </div>
                )
              })}

              <div
                className="mt-4 rounded-md px-3 py-2 text-[11px]"
                style={{
                  border: '1px dashed rgba(242,194,0,.45)',
                  color: 'rgba(242,194,0,.85)',
                }}
              >
                Strands Agents (AWS) orchestrates every step
              </div>
            </div>
          </div>
        </div>

        {/* ---------------------------------------------------- detail panel */}
        <div
          style={{
            flex: squeeze,
            minWidth: 0,
            position: 'relative',
            // a definite height so the card can cover the description exactly rather than
            // resizing the row as it arrives
            minHeight: 420,
            opacity: squeeze,
            overflow: 'hidden',
          }}
        >
          {/* ---- beat one: the argument ---- */}
          <div
            style={{
              opacity: panel * (1 - card * 0.9),
              transform: `translate3d(0, ${(1 - panel) * 14 - card * 18}px, 0)`,
            }}
          >
          <p className="text-xs uppercase tracking-[0.22em] text-white/35">
            Step {active + 1} of {STEPS.length}
          </p>
          <h3 className="mt-3 text-4xl font-bold tracking-tight text-white">
            {STEPS[active].label}
          </h3>
          <p className="mt-2 text-sm text-white/45">{STEPS[active].tool}</p>

          <div
            className="mt-6 rounded-lg px-5 py-4"
            style={{
              background: 'rgba(242,194,0,.07)',
              borderLeft: '3px solid #f2c200',
            }}
          >
            <p className="text-[11px] uppercase tracking-[0.2em] text-[#f2c200]">
              Why this tool
            </p>
            <p className="mt-2 text-[14px] leading-relaxed text-white/80">
              {STEPS[active].why}
            </p>
          </div>

          <ul className="mt-6 space-y-3">
            {STEPS[active].detail.map((line) => (
              <li
                key={line}
                className="pl-4 text-[14px] leading-relaxed text-white/70"
                style={{ borderLeft: '2px solid rgba(255,255,255,.18)' }}
              >
                {line}
              </li>
            ))}
          </ul>
          </div>

          {/* ---- beat two: the card slides over ---- */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              opacity: card * panel,
              transform: `translate3d(0, ${(1 - card) * 46}px, 0)`,
              pointerEvents: card < 0.5 ? 'none' : 'auto',
            }}
          >
            <HazardFrame thickness={3} radius={12} stripe={9} style={{ width: '100%' }}>
              <div style={{ background: '#0d0d0d', padding: '18px 20px' }}>
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                    {step.pair
                      ? 'same fingerprint, different worlds'
                      : step.video
                      ? 'real footage · NVIDIA PhysicalAI'
                      : step.graphic
                        ? 'what the graph actually looks like'
                        : `${step.code.lang} · from the repo`}
                  </span>
                  <span className="text-[10px] text-[#f2c200]">{step.label}</span>
                </div>

                {step.pair ? (
                  <div>
                    <div className="grid grid-cols-2 gap-3">
                      {[step.pair.left, step.pair.right].map((v) => (
                        <figure key={v.src} style={{ margin: 0 }}>
                          <video
                            src={v.src}
                            autoPlay loop muted playsInline
                            style={{ width: '100%', borderRadius: 6, display: 'block' }}
                          />
                          <figcaption className="mt-2 text-[10.5px] text-white/45">
                            {v.label}
                          </figcaption>
                        </figure>
                      ))}
                    </div>
                    <div
                      className="mt-3 rounded-md px-3 py-2 text-center text-[12px]"
                      style={{ background: 'rgba(242,194,0,.1)', color: '#f2c200',
                               fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}
                    >
                      fingerprint {step.pair.fingerprint}
                    </div>
                    <p className="mt-3 text-[11.5px] leading-relaxed text-white/50">
                      {step.pair.caption}
                    </p>
                  </div>
                ) : step.video ? (
                  <figure style={{ margin: 0 }}>
                    <video
                      key={step.video.src}
                      src={step.video.src}
                      autoPlay
                      loop
                      muted
                      playsInline
                      style={{ width: '100%', borderRadius: 6, display: 'block' }}
                    />
                    <figcaption className="mt-3 text-[11.5px] leading-relaxed text-white/50">
                      {step.video.caption}
                    </figcaption>
                  </figure>
                ) : step.graphic === 'schema' ? (
                  <div>
                    <GraphSchema height={230} />
                    <p className="mt-2 text-[11.5px] leading-relaxed text-white/50">
                      Every question starts at an Event and walks outward.
                      <span style={{ color: '#f2c200' }}> MISSING_CONTROL</span> is the edge
                      that carries absence — which is why this is a graph and not a table.
                    </p>
                  </div>
                ) : (
                  <pre
                    className="overflow-x-auto text-[11.5px] leading-relaxed"
                    style={{
                      color: 'rgba(255,255,255,.8)',
                      fontFamily:
                        'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                      margin: 0,
                    }}
                  >
                    <code>{step.code.body}</code>
                  </pre>
                )}
              </div>
            </HazardFrame>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'

import { HazardFrame } from '@/components/HazardFrame'
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

export const PIPELINE_AT = 0.52
const SQUEEZE_FROM = 0.56
const SQUEEZE_TO = 0.60
const STEP_SPAN = 0.048

type Step = {
  id: string
  label: string
  tool: string
  aws?: boolean
  call: string
  handoff: string
  /** Why this tool and not something simpler. The question a judge asks first. */
  why: string
  detail: string[]
}

const STEPS: Step[] = [
  {
    id: 'watch',
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

function activeIndex(progress: number) {
  const i = Math.floor((progress - SQUEEZE_TO) / STEP_SPAN)
  return Math.min(STEPS.length - 1, Math.max(0, i))
}

export function PipelineSection({ progress }: { progress: number }) {
  // Hands the stage to the demo once the last step has had its turn.
  const sectionOpacity =
    remap(progress, PIPELINE_AT - 0.03, PIPELINE_AT, 0, 1) *
    (1 - remap(progress, 0.79, 0.82, 0, 1))
  const squeeze = remap(progress, SQUEEZE_FROM, SQUEEZE_TO, 0, 1)
  const active = activeIndex(progress)

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
                const isActive = squeeze > 0.5 && i === active
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
            opacity: squeeze,
            overflow: 'hidden',
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
            className="mt-5 rounded-lg px-4 py-3 text-[12px] text-white/70"
            style={{
              background: 'rgba(255,255,255,.05)',
              border: '1px solid rgba(255,255,255,.1)',
              fontFamily:
                'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            }}
          >
            {STEPS[active].call}
          </div>

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

          <ul className="mt-6 space-y-4">
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
      </div>
    </div>
  )
}

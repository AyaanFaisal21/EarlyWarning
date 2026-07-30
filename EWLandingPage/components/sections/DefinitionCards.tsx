'use client'

import { HazardFrame } from '@/components/HazardFrame'
import { remap } from '@/lib/useScrollProgress'

/**
 * The three-tier severity ladder, revealed one card at a time as the reader scrolls.
 *
 * Cards accumulate rather than replace each other — by the end all three are on screen
 * together, because the point is the comparison between them, not any one definition.
 *
 * Note on the source material: the standard poster version of this ends with "all accidents
 * start as near misses". We deliberately do not say that. It is the Heinrich causal-chain
 * claim, and the evidence does not support it — minor-event frequency and serious-injury
 * frequency move independently. The definitions themselves are uncontroversial; the causal
 * ladder is not. See SAFETY_EVIDENCE.md.
 */

type Tier = {
  name: string
  definition: string
  example: string
  matters: string
  emphasis?: boolean
}

// Ordered worst-first, so the reader arrives at the near miss last.
//
// The obvious ordering escalates toward the accident, which makes the accident the point.
// It isn't. Running it backwards — consequence, then damage, then the one where nothing
// happened at all — means the section lands on the only tier still worth acting on, and
// the reader gets there by elimination rather than being told.
const TIERS: Tier[] = [
  {
    name: 'Accident',
    definition:
      'An unplanned event that results in injury, illness, or property loss.',
    example: 'A worker falls from a ladder and fractures a leg.',
    matters:
      'Now it is a claim, an investigation, and a person who got hurt. Everything after this point is cleanup.',
  },
  {
    name: 'Incident',
    definition:
      'An unplanned event that disrupts work or damages property, with nobody hurt.',
    example:
      'A forklift clips a racking upright. Stock is damaged; no one is injured.',
    matters:
      'Something visible broke, so it gets investigated. The control that failed was already failing before this.',
  },
  {
    name: 'Near miss',
    definition:
      'An unplanned event that caused no injury and no damage — but could have.',
    example:
      'A worker slips on a wet floor, catches their balance, and walks on.',
    matters:
      'Nothing happened, so nothing gets filed. This is the tier the record never sees, and the only one where intervention is still cheap.',
    emphasis: true,
  },
]

// Each card starts its entrance a little after the previous one.
const FIRST_AT = 0.37
const STAGGER = 0.04
const RAMP = 0.04
const FADE_OUT_AT = 0.48

export function DefinitionCards({ progress }: { progress: number }) {
  // Fades out to hand the stage to the pipeline, otherwise both render at once.
  const sectionOpacity =
    remap(progress, FIRST_AT - 0.04, FIRST_AT, 0, 1) *
    (1 - remap(progress, FADE_OUT_AT, FADE_OUT_AT + 0.04, 0, 1))

  return (
    <div
      className="pointer-events-none flex items-center justify-center px-6"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 12,
        opacity: sectionOpacity,
      }}
    >
      <div className="mx-auto w-full max-w-6xl">
        <p className="mb-10 text-sm uppercase tracking-[0.2em] text-white/40">
          Three tiers. Only one is still preventable.
        </p>

        <div className="grid items-stretch gap-5 md:grid-cols-3">
          {TIERS.map((tier, i) => {
            const start = FIRST_AT + i * STAGGER
            const t = remap(progress, start, start + RAMP, 0, 1)

            const body = (
              <div
                style={{
                  background: tier.emphasis ? '#ffffff' : 'transparent',
                  color: tier.emphasis ? '#0a0a0a' : '#ffffff',
                  padding: '26px 24px',
                  height: '100%',
                }}
              >
                <h3 className="text-2xl font-bold tracking-tight">{tier.name}</h3>

                <p
                  className="mt-4 text-[15px] leading-relaxed"
                  style={{ opacity: tier.emphasis ? 0.85 : 0.8 }}
                >
                  {tier.definition}
                </p>

                <p
                  className="mt-5 text-[13px] leading-relaxed"
                  style={{ opacity: tier.emphasis ? 0.6 : 0.5 }}
                >
                  {tier.example}
                </p>

                <div
                  className="mt-5 pt-4 text-[13px] leading-relaxed"
                  style={{
                    borderTop: tier.emphasis
                      ? '1px solid rgba(10,10,10,.14)'
                      : '1px solid rgba(255,255,255,.16)',
                    opacity: tier.emphasis ? 0.9 : 0.62,
                  }}
                >
                  {tier.matters}
                </div>
              </div>
            )

            return (
              <article
                key={tier.name}
                style={{
                  opacity: t,
                  transform: `translate3d(0, ${(1 - t) * 36}px, 0)`,
                  willChange: 'transform, opacity',
                }}
              >
                {tier.emphasis ? (
                  // Same caution border as the header — this is the card the product is
                  // about, and the yellow is the page's only accent, so spending it here
                  // ties the two together.
                  <HazardFrame thickness={4} radius={14} style={{ height: '100%' }}>
                    {body}
                  </HazardFrame>
                ) : (
                  <div
                    style={{
                      border: '1px solid rgba(255,255,255,.22)',
                      borderRadius: 14,
                      overflow: 'hidden',
                      height: '100%',
                    }}
                  >
                    {body}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </div>
    </div>
  )
}

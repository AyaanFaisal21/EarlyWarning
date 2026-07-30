'use client'

import { HazardFrame } from '@/components/HazardFrame'
import { BANDS, band, reveal } from '@/lib/timeline'

/**
 * The whole argument in three lines, before a single number.
 *
 * Deliberately ahead of the statistics. Numbers that back up a claim already made are far
 * more persuasive than numbers building toward one, and an audience reading a chart while
 * someone talks over it follows neither.
 *
 * The three beats are: the human gap, the machine gap, and the asset that already exists.
 * The third is not a market claim — it is the observation that the footage is already being
 * recorded and nobody watches it. That lands harder than asserting a market, and it is
 * simply true.
 *
 * Note the autonomous-machinery line is a CLAIM only. The evidence for it lives on the
 * closing section, behind "you think this is just about what's happening now?" — setup here,
 * payoff there.
 */

// Derived, not pinned. This was hard-coded to the old band start, so reordering
// the sections would have stranded every reveal mid-fade.
const AT = BANDS.thesis[0] + 0.04

const LINES = [
  {
    text: 'A near miss is almost never reported by the person it nearly happened to. So the same event is invited back — until one time it isn’t a near miss.',
    at: 0,
  },
  {
    text: 'Autonomous machinery is arriving on those same floors. It will cause near misses too, and it won’t report them either. At best, it records them.',
    at: 0.03,
  },
  {
    text: 'That footage already exists. Nobody has the hours to watch it.',
    at: 0.06,
    emphasis: true,
  },
]

export function ThesisSection({ progress }: { progress: number }) {
  const opacity = band(progress, 'thesis')

  return (
    <div
      className="flex items-center justify-center px-6"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 10,
        opacity,
        pointerEvents: opacity < 0.1 ? 'none' : 'auto',
      }}
    >
      <div className="mx-auto w-full" style={{ maxWidth: 940 }}>
        <p className="text-xs uppercase tracking-[0.22em] text-white/35">
          The problem, and what it costs
        </p>

        <div className="mt-8 space-y-7">
          {LINES.map((line) => {
            const t = reveal(progress, 'thesis', AT + line.at)
            return (
              <p
                key={line.text}
                className={
                  line.emphasis
                    ? 'text-2xl font-bold leading-snug tracking-tight text-white md:text-3xl'
                    : 'text-xl leading-relaxed text-white/70 md:text-2xl'
                }
                style={{
                  opacity: t,
                  transform: `translate3d(0, ${(1 - t) * 20}px, 0)`,
                }}
              >
                {line.text}
              </p>
            )
          })}
        </div>

        <div
          style={{
            // reveal() clamps this so it always lands before the section fades
            opacity: reveal(progress, 'thesis', AT + 0.09),
          }}
        >
          <HazardFrame thickness={4} radius={14} className="mt-10 inline-block">
            <div style={{ background: '#ffffff', color: '#0a0a0a', padding: '18px 26px' }}>
              <p className="max-w-2xl text-[15px] font-medium leading-relaxed">
                Early Warning reads the recordings nobody opens and surfaces the near misses
                nobody filed — before the event that follows them.
              </p>
            </div>
          </HazardFrame>
        </div>
      </div>
    </div>
  )
}

'use client'

import { HazardFrame } from '@/components/HazardFrame'
import { band } from '@/lib/timeline'

/**
 * The closer: why this gets harder, not easier.
 *
 * The argument is deliberately not "AI will fix safety". It is that the floor is about to
 * fill with machines that do not file reports either, and that the only instrument which
 * sees both parties in the same frame is the camera that is already up there.
 */



const FACTS = [
  {
    figure: '$29.98B → $65.74B',
    label: 'warehouse automation market, 2025 to 2031',
  },
  {
    figure: '1.3M',
    label: 'robotics-as-a-service installations projected by 2026',
  },
  {
    figure: '13%',
    label: 'of warehouses will have deployed even one fulfilment AMR by 2030',
  },
]

export function FutureSection({ progress }: { progress: number }) {
  const opacity = band(progress, 'future')

  return (
    <div
      className="flex items-center justify-center px-6"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 18,
        opacity,
        pointerEvents: opacity < 0.1 ? 'none' : 'auto',
      }}
    >
      <div className="mx-auto w-full" style={{ maxWidth: 1000 }}>
        {/* The opening section already CLAIMED that autonomous machinery makes this worse.
            This is where the claim gets paid off, so it opens by pointing back at it. */}
        <p className="text-lg leading-relaxed text-white/55 md:text-xl">
          You think this is just about what&apos;s happening now?
        </p>
        <p className="mt-2 text-lg leading-relaxed text-white/55 md:text-xl">
          Take a look at what&apos;s slated for workplaces.
        </p>

        <h3 className="mt-8 max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white md:text-5xl">
          The floor is about to fill with machines that don&apos;t file reports either.
        </h3>

        <div className="mt-9 grid gap-6 md:grid-cols-3">
          {FACTS.map((f) => (
            <div key={f.label} style={{ borderLeft: '1px solid rgba(255,255,255,.2)', paddingLeft: 18 }}>
              <div className="text-2xl font-bold tracking-tight text-white">{f.figure}</div>
              <p className="mt-2 text-[13px] leading-relaxed text-white/55">{f.label}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 max-w-3xl space-y-4 text-[15px] leading-relaxed text-white/70">
          <p>
            That last number is the one that matters. The mixing of people and autonomous
            equipment is almost entirely ahead of us — and the research says plainly that
            collision-avoidance still needs a better model of how workers actually behave
            around moving machines.
          </p>
          <p>
            A robot logs its own telemetry. It records that it stopped. It cannot record
            that a person was already stepping into its path, or that the walkway marking
            wore away six weeks ago. The worker will not file that either — not out of
            negligence, but because nothing happened.
          </p>
        </div>

        <HazardFrame thickness={4} radius={14} className="mt-9 inline-block">
          <div style={{ background: '#ffffff', color: '#0a0a0a', padding: '20px 26px' }}>
            <p className="max-w-2xl text-[15px] font-medium leading-relaxed">
              Both parties to the next decade of workplace accidents are bad at reporting
              them. The camera on the ceiling is the only witness that sees both.
            </p>
          </div>
        </HazardFrame>
      </div>
    </div>
  )
}

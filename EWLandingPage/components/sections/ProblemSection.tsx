'use client'

import { HazardFrame } from '@/components/HazardFrame'
import { band } from '@/lib/timeline'

/**
 * Problem statement, the numbers, and why counting failed — one page.
 *
 * The headline pairing is deliberate: total workplace deaths FELL while the specific
 * category this system watches ROSE 19%. A single scary number is easy to wave away; two
 * numbers moving in opposite directions is an argument.
 *
 * Sources, all verifiable:
 *   BLS Census of Fatal Occupational Injuries 2024
 *   Liberty Mutual Workplace Safety Index 2025 (reflects 2022 data)
 *   Benchmark Gensuite 2026 EHS Benchmarking Report
 *   National Safety Council
 */



const NUMBERS = [
  { figure: '5,070', label: 'fatal work injuries in the US in 2024', note: 'down 4% year on year' },
  { figure: '+19%', label: 'pedestrians struck by vehicles at work', note: '369, up from 310', alarm: true },
  { figure: '90%', label: 'of near misses are never reported', note: 'other studies say 50–90%' },
  { figure: '$1B', label: 'paid weekly in direct workers’ comp', note: '$58.8B a year' },
]

export function ProblemSection({ progress }: { progress: number }) {
  const opacity = band(progress, 'problem')

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
      <div className="mx-auto w-full" style={{ maxWidth: 1080 }}>
        <p className="text-xs uppercase tracking-[0.22em] text-white/35">The problem</p>

        <h2 className="mt-4 max-w-4xl text-4xl font-bold leading-tight tracking-tight text-white md:text-5xl">
          Workplace deaths are falling. Being struck by a vehicle at work is not.
        </h2>

        <div className="mt-9 grid gap-6 md:grid-cols-4">
          {NUMBERS.map((n) => (
            <div
              key={n.label}
              style={{
                borderLeft: `2px solid ${n.alarm ? '#f2c200' : 'rgba(255,255,255,.2)'}`,
                paddingLeft: 16,
              }}
            >
              <div
                className="text-3xl font-bold tracking-tight md:text-4xl"
                style={{ color: n.alarm ? '#f2c200' : '#ffffff' }}
              >
                {n.figure}
              </div>
              <p className="mt-2 text-[13px] leading-snug text-white/65">{n.label}</p>
              <p className="mt-1 text-[11px] text-white/35">{n.note}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-8 md:grid-cols-2">
          <div className="space-y-4 text-[15px] leading-relaxed text-white/70">
            <p>
              Every one of those deaths was preceded by events where nothing happened. The
              forklift stopped. The worker stepped back. The load swung past. The National
              Safety Council puts it at <strong className="text-white">75% of accidents
              preceded by at least one near miss</strong>.
            </p>
            <p>
              None of it gets filed — not from negligence, but because there is nothing to
              file. A better form does not fix a recognition failure.
            </p>
          </div>

          <div className="space-y-4 text-[15px] leading-relaxed text-white/70">
            <p>
              <strong className="text-white">The obvious fix already failed.</strong> Counting
              near misses was the strategy for ninety years. Minor injuries fell for decades
              while serious injuries and fatalities did not follow.
            </p>
            <p>
              So the field moved to <strong className="text-white">SIF potential</strong> —
              not how many, but which ones could have killed someone. That is a judgement
              about a scene, not a tally. Which is exactly why it is still a human job.
            </p>
          </div>
        </div>

        <HazardFrame thickness={3} radius={12} className="mt-9 inline-block">
          <div style={{ background: '#ffffff', color: '#0a0a0a', padding: '14px 22px' }}>
            <p className="text-[14px] font-medium">
              Judging what nearly happened means watching. Nobody has the hours.
            </p>
          </div>
        </HazardFrame>
      </div>
    </div>
  )
}

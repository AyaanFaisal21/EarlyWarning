'use client'

import { HazardFrame } from '@/components/HazardFrame'
import { remap } from '@/lib/useScrollProgress'

/**
 * Slot for the recorded walkthrough.
 *
 * Drop a file at /public/demo.mp4 and it plays here; until then the frame shows what the
 * recording needs to contain, so the placeholder is a shot list rather than dead space.
 *
 * Deliberately a recording and not a live pipeline run: ingest takes ~25s per clip and the
 * graph write is instant, so a live attempt on stage is three minutes of watching a
 * progress bar. A cut recording shows the same truth in forty seconds, and nothing about it
 * can fail on venue wifi.
 */

export const DEMO_AT = 0.82

const BEATS = [
  'Raw CCTV going in — the clip nobody would have watched',
  'Pegasus returning structured rows: hazard, absent controls, counterfactual',
  'The fingerprint resolving one event into an existing pattern',
  'Nodes and edges landing in the Neo4j graph, live',
  'The brief coming back out: named cause, and one action for this week',
]

export function DemoSection({
  progress,
  src = '/demo.mp4',
  graphUrl = 'https://console.neo4j.io',
}: {
  progress: number
  src?: string
  graphUrl?: string
}) {
  const opacity =
    remap(progress, DEMO_AT - 0.03, DEMO_AT, 0, 1) *
    (1 - remap(progress, 0.9, 0.93, 0, 1))

  return (
    <div
      className="flex items-center justify-center px-6"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 16,
        opacity,
        pointerEvents: opacity < 0.1 ? 'none' : 'auto',
      }}
    >
      <div className="mx-auto w-full" style={{ maxWidth: 1100 }}>
        <p className="text-xs uppercase tracking-[0.22em] text-white/35">
          End to end, on real footage
        </p>
        <h3 className="mt-3 text-4xl font-bold tracking-tight text-white">
          Watch it run
        </h3>

        <div className="mt-7 grid gap-7 md:grid-cols-[1.6fr_1fr]">
          <HazardFrame thickness={4} radius={14}>
            <div style={{ background: '#0d0d0d', aspectRatio: '16 / 9' }}>
              <video
                src={src}
                controls
                playsInline
                preload="metadata"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            </div>
          </HazardFrame>

          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-white/35">
              What you are watching
            </p>
            <ol className="mt-4 space-y-3">
              {BEATS.map((beat, i) => (
                <li key={beat} className="flex gap-3 text-[13px] leading-relaxed text-white/70">
                  <span className="shrink-0 font-mono text-[11px] text-[#f2c200]">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  {beat}
                </li>
              ))}
            </ol>

            <a
              href={graphUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-flex items-center gap-2 rounded-md px-4 py-2 text-[13px] font-medium transition-opacity hover:opacity-80"
              style={{ background: '#f2c200', color: '#0a0a0a' }}
            >
              Open the live graph ↗
            </a>
            <p className="mt-2 text-[11px] leading-relaxed text-white/35">
              Opens Neo4j directly — the same instance the pipeline writes to.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

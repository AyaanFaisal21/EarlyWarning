'use client'

import { Manrope } from 'next/font/google'

import { HAZARD_YELLOW, HazardFrame } from '@/components/HazardFrame'
import { GraphSceneClient } from '@/components/scene/GraphSceneClient'
import { DefinitionCards } from '@/components/sections/DefinitionCards'
import { ProblemSection } from '@/components/sections/ProblemSection'
import { ThesisSection } from '@/components/sections/ThesisSection'
import { FutureSection } from '@/components/sections/FutureSection'
import { PipelineSection } from '@/components/sections/PipelineSection'
import { TileField } from '@/components/sections/TileField'
import { scrollToBand } from '@/lib/timeline'
import { remap, useScrollProgress } from '@/lib/useScrollProgress'

const manrope = Manrope({ subsets: ['latin'] })

/**
 * Explicit viewport sizing rather than `fixed inset-0`.
 *
 * The R3F <Canvas> measures its parent to size its drawing buffer. With inset-based
 * stretching the parent resolves to 0x0 at mount, the canvas silently falls back to its
 * 300x150 default, and you get a blank page with no error anywhere. Concrete vw/vh units
 * give it something to measure on the first pass.
 */
const FULLSCREEN: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
}

/**
 * Scroll choreography, all driven off one normalised progress value:
 *
 *   0.00 - 0.35   camera dollies from a wide shot into the grid
 *   0.16 - 0.32   hero copy fades out
 *   0.30 - 0.42   3D canvas fades out behind it
 *   0.42+         black tiles sweep in and become the backdrop for the content below
 *
 * The ranges overlap on purpose — the canvas is already fading while the camera is still
 * moving, so the handoff reads as one continuous move rather than two animations in a row.
 */
export default function Component() {
  const progress = useScrollProgress()

  const heroOpacity = 1 - remap(progress, 0.05, 0.10, 0, 1)
  const canvasOpacity = 1 - remap(progress, 0.11, 0.14, 0, 1)

  return (
    <div className={`relative text-white ${manrope.className}`}>
      {/* tall enough to give the choreography room to breathe */}
      <div style={{ height: '1900vh' }}>
        <TileField progress={progress} />

        <div style={{ ...FULLSCREEN, zIndex: 1, opacity: canvasOpacity, transition: 'opacity 240ms linear' }}>
          <GraphSceneClient progress={progress} />
        </div>

        {/*
          Solid dark bar rather than bare text on the page.
          The background travels from white to black across the scroll, so any header that
          inherits the page colour is unreadable at one end or the other. Giving the bar its
          own dark base and white type makes it legible the whole way down and needs no
          colour interpolation.
        */}
        <header
          className="fixed left-0 right-0 top-0 flex justify-center px-4 pt-4"
          style={{ zIndex: 30 }}
        >
          <HazardFrame
            className="w-full max-w-6xl"
            style={{ boxShadow: '0 1px 2px rgba(0,0,0,.28), 0 8px 28px rgba(0,0,0,.16)' }}
          >
            <nav
              className="flex w-full items-center justify-between px-6 py-4 text-white"
              style={{ background: '#0a0a0a' }}
            >
              <a
                href="#top"
                onClick={(e) => {
                  e.preventDefault()
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                className="flex items-center gap-3 transition-opacity hover:opacity-70"
                aria-label="Back to top"
              >
                <span
                  className="inline-block h-3 w-3"
                  style={{ background: HAZARD_YELLOW }}
                />
                <span className="text-lg font-bold tracking-tight">Early Warning</span>
              </a>
              <ul className="hidden gap-8 text-sm text-white/70 md:flex">
                {([
                  ['Problem', 'thesis'],
                  ['How it works', 'pipeline'],
                  ['What\u2019s next', 'future'],
                ] as const).map(([label, target]) => (
                  <li key={label}>
                    <button
                      type="button"
                      onClick={() => scrollToBand(target)}
                      className="transition-colors hover:text-white"
                    >
                      {label}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </HazardFrame>
        </header>

        {/* ---------------------------------------------------------------- hero */}
        <section
          className="flex flex-col items-center justify-center px-6 text-center"
          style={{
            ...FULLSCREEN,
            zIndex: 10,
            opacity: heroOpacity,
            pointerEvents: heroOpacity < 0.1 ? 'none' : 'auto',
          }}
        >
          <h1 className="mx-auto max-w-4xl text-6xl font-bold leading-[1.05] tracking-tight md:text-7xl">
            The incidents nobody reported
          </h1>
          <p className="mt-8 max-w-2xl text-lg text-white/60 md:text-xl">
            Near misses are supposed to be a leading indicator. They can&apos;t be, if nobody
            files them.
          </p>
          <div className="mt-12 flex items-center gap-3 text-sm text-white/45">
            <span className="h-px w-8 bg-white/35" />
            scroll
          </div>
        </section>

        <ThesisSection progress={progress} />
        <ProblemSection progress={progress} />

        <DefinitionCards progress={progress} />
        <PipelineSection progress={progress} />
        <FutureSection progress={progress} />
      </div>
    </div>
  )
}

'use client'

import { useMemo } from 'react'

/**
 * The field of black squares that slides in to become the background for everything below
 * the fold.
 *
 * Deliberately DOM + CSS rather than more three.js: this is a static backdrop that content
 * sits on top of, and a second WebGL canvas would cost a context, fight the first one for
 * the compositor, and gain nothing visually. Transform and opacity only, so it stays on the
 * GPU compositor and never triggers layout.
 *
 * Offsets are derived from the tile index rather than Math.random so server and client
 * markup agree — random here is a hydration mismatch in Next.js.
 */
export function TileField({ progress, cols = 16, rows = 10 }: {
  progress: number
  cols?: number
  rows?: number
}) {
  const tiles = useMemo(() => {
    const out: { key: number; dx: number; dy: number; delay: number }[] = []
    for (let i = 0; i < cols * rows; i++) {
      // cheap deterministic hash -> stable pseudo-random direction per tile
      const h = Math.sin(i * 12.9898) * 43758.5453
      const f = h - Math.floor(h)
      const angle = f * Math.PI * 2
      const row = Math.floor(i / cols)
      out.push({
        key: i,
        dx: Math.cos(angle) * 140,
        dy: Math.sin(angle) * 140,
        // diagonal sweep so they arrive as a wave rather than all at once
        delay: (row + (i % cols)) * 14,
      })
    }
    return out
  }, [cols, rows])

  const settled = progress > 0.10

  return (
    <div
      aria-hidden
      className="pointer-events-none"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        gap: '2px',
        padding: '2px',
        // White while the tiles are still arriving, so the gaps read as a grid mid-flight;
        // black once they land, so the 2px seams disappear and the screen is genuinely
        // black rather than black squares on a white lattice.
        background: settled ? '#0a0a0a' : '#232323',
        transition: 'background 700ms ease 320ms',
      }}
    >
      {tiles.map((t) => (
        <div
          key={t.key}
          style={{
            background: '#0a0a0a',
            opacity: settled ? 1 : 0,
            transform: settled
              ? 'translate3d(0,0,0) scale(1)'
              : `translate3d(${t.dx}px, ${t.dy}px, 0) scale(0.6)`,
            transition: `transform 620ms cubic-bezier(.22,.61,.36,1) ${t.delay}ms, opacity 420ms ease ${t.delay}ms`,
            willChange: 'transform, opacity',
          }}
        />
      ))}
    </div>
  )
}

'use client'

/**
 * The graph schema, drawn in the site's palette.
 *
 * Rendered rather than screenshotted from Neo4j Browser on purpose: the Browser's pastel
 * defaults sit *on top of* a black-and-yellow page instead of inside it, and a screenshot
 * cannot be restyled or made responsive. This is the same shape, in the same ink.
 *
 * Event is the hub because every question the product asks starts from an event and walks
 * outward. MISSING_CONTROL is drawn in hazard yellow — it is the edge that carries absence,
 * which is the whole reason this is a graph and not a table.
 */

const YELLOW = '#f2c200'

type Spoke = {
  label: string
  rel: string
  x: number
  y: number
  accent?: boolean
}

const SPOKES: Spoke[] = [
  { label: 'Pattern', rel: 'INSTANCE_OF', x: 150, y: 60 },
  { label: 'Actor', rel: 'INVOLVED', x: 470, y: 60 },
  { label: 'Hazard\nType', rel: 'OF_TYPE', x: 530, y: 235 },
  { label: 'Control', rel: 'MISSING_CONTROL', x: 90, y: 235, accent: true },
]

const HUB = { x: 310, y: 160 }

export function GraphSchema({ height = 300 }: { height?: number }) {
  return (
    <svg
      viewBox="0 0 620 320"
      style={{ width: '100%', height, display: 'block' }}
      role="img"
      aria-label="Event node connected to Pattern, Actor, Hazard Type and Control"
    >
      <defs>
        <marker id="ew-arrow" viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,.45)" />
        </marker>
        <marker id="ew-arrow-hot" viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill={YELLOW} />
        </marker>
      </defs>

      {SPOKES.map((s) => {
        // stop the line short of both circles so the arrowhead meets the rim, not the centre
        const dx = s.x - HUB.x
        const dy = s.y - HUB.y
        const len = Math.hypot(dx, dy)
        const [ux, uy] = [dx / len, dy / len]
        const x1 = HUB.x + ux * 52
        const y1 = HUB.y + uy * 52
        const x2 = s.x - ux * 46
        const y2 = s.y - uy * 46
        const mx = (x1 + x2) / 2
        const my = (y1 + y2) / 2
        const angle = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI

        return (
          <g key={s.rel}>
            <line
              x1={x1} y1={y1} x2={x2} y2={y2}
              stroke={s.accent ? YELLOW : 'rgba(255,255,255,.28)'}
              strokeWidth={s.accent ? 1.6 : 1.2}
              markerEnd={s.accent ? 'url(#ew-arrow-hot)' : 'url(#ew-arrow)'}
            />
            <text
              x={mx} y={my - 6}
              transform={`rotate(${angle > 90 || angle < -90 ? angle + 180 : angle} ${mx} ${my})`}
              textAnchor="middle"
              fontSize="9.5"
              letterSpacing="0.08em"
              fill={s.accent ? YELLOW : 'rgba(255,255,255,.4)'}
              fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
            >
              {s.rel}
            </text>

            <circle
              cx={s.x} cy={s.y} r={44}
              fill="#141414"
              stroke={s.accent ? YELLOW : 'rgba(255,255,255,.3)'}
              strokeWidth={s.accent ? 1.6 : 1}
            />
            {s.label.split('\n').map((word, i, all) => (
              <text
                key={word}
                x={s.x}
                y={s.y + 4 + (i - (all.length - 1) / 2) * 13}
                textAnchor="middle"
                fontSize="12.5"
                fill={s.accent ? YELLOW : 'rgba(255,255,255,.85)'}
              >
                {word}
              </text>
            ))}
          </g>
        )
      })}

      <circle cx={HUB.x} cy={HUB.y} r={50} fill="#ffffff" />
      <text x={HUB.x} y={HUB.y + 5} textAnchor="middle" fontSize="14"
            fontWeight="700" fill="#0a0a0a">
        Event
      </text>
    </svg>
  )
}

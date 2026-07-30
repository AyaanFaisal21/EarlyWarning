'use client'

import type { CSSProperties, ReactNode } from 'react'

/**
 * Caution-tape border: diagonal yellow/black stripes framing whatever it wraps.
 *
 * Built as a padded outer element carrying the stripe gradient, with the child sitting on
 * its own opaque background inset by `thickness`. That is what makes it read as a *border*
 * rather than a striped panel — the stripes only survive in the gap.
 *
 * The inner radius is deliberately `radius - thickness`. Matching radii leaves the corners
 * looking pinched because the outer curve is longer than the inner one.
 *
 * One yellow on an otherwise black-and-white page is the entire accent budget. Keep it.
 */

export const HAZARD_YELLOW = '#f2c200'

export function HazardFrame({
  children,
  thickness = 4,
  radius = 14,
  stripe = 10,
  animate = true,
  className,
  style,
}: {
  children: ReactNode
  thickness?: number
  radius?: number
  stripe?: number
  animate?: boolean
  className?: string
  style?: CSSProperties
}) {
  return (
    <div
      className={className}
      style={{
        padding: thickness,
        borderRadius: radius,
        background: `repeating-linear-gradient(45deg, ${HAZARD_YELLOW} 0 ${stripe}px, #0a0a0a ${stripe}px ${stripe * 2}px)`,
        // One stripe period per cycle, so the loop is seamless — any other distance
        // visibly jumps at the wrap.
        backgroundSize: `${stripe * 2 * Math.SQRT2}px ${stripe * 2 * Math.SQRT2}px`,
        animation: animate ? 'hazard-march 2.4s linear infinite' : undefined,
        ...style,
      }}
    >
      <div style={{ borderRadius: Math.max(0, radius - thickness), overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  )
}

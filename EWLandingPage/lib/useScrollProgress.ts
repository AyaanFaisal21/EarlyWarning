'use client'

import { useEffect, useState } from 'react'

/**
 * Normalised scroll position, 0 at the top of the document and 1 at the bottom.
 *
 * Read once here and passed down rather than each component attaching its own listener —
 * several things animate off the same value (camera dolly, hero fade, tile reveal) and they
 * must stay in lockstep. Separate listeners drift.
 */
export function useScrollProgress() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let frame = 0

    const read = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight
      setProgress(scrollable > 0 ? window.scrollY / scrollable : 0)
      frame = 0
    }

    // rAF-coalesced: scroll fires far more often than the screen repaints, and setState
    // per event makes the camera stutter on a trackpad.
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(read)
    }

    read()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (frame) cancelAnimationFrame(frame)
    }
  }, [])

  return progress
}

/** Map `value` from [inMin,inMax] onto [outMin,outMax], clamped at both ends. */
export function remap(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
) {
  if (inMax === inMin) return outMin
  const t = Math.min(1, Math.max(0, (value - inMin) / (inMax - inMin)))
  return outMin + t * (outMax - outMin)
}

import { remap } from './useScrollProgress'

/**
 * Every scroll window on the page, in one file.
 *
 * These numbers used to live inside each section, and they drifted apart: the thesis faded
 * out at 0.33 while its own last line was still arriving at 0.34, so nobody ever saw it.
 * The definition cards had the same defect. That class of bug is invisible in code review
 * and obvious the moment you scroll, which is exactly why the numbers belong side by side
 * where the overlap is visible.
 *
 * Each band is [enter, exit]. A section fades in over FADE before `enter`, holds, and fades
 * out over FADE before `exit`. Anything revealed *inside* a section must finish before
 * `exit - FADE`, or it appears and disappears in the same breath — see assertHoldsUntil.
 */

export const FADE = 0.03

export const BANDS = {
  //            enter  exit
  thesis:   [0.13, 0.30] as const,
  problem:  [0.32, 0.45] as const,
  cards:    [0.47, 0.58] as const,
  pipeline: [0.60, 0.88] as const,
  future:   [0.90, 1.01] as const,
}

export type BandName = keyof typeof BANDS

/** Opacity for a whole section: fade in before `enter`, fade out before `exit`. */
export function band(progress: number, name: BandName) {
  const [enter, exit] = BANDS[name]
  return (
    remap(progress, enter - FADE, enter, 0, 1) *
    (1 - remap(progress, exit - FADE, exit, 0, 1))
  )
}

/** The last moment a section is still fully opaque — reveals must land before this. */
export function holdsUntil(name: BandName) {
  return BANDS[name][1] - FADE
}

/**
 * Reveal a piece of content at `at`, guaranteed to finish while its section is still
 * readable. If a caller asks for a reveal that would land during the fade-out, it is pulled
 * earlier rather than silently rendering something nobody can see.
 */
export function reveal(progress: number, name: BandName, at: number, ramp = 0.02) {
  const latest = holdsUntil(name) - ramp - 0.01
  const start = Math.min(at, latest)
  return remap(progress, start, start + ramp, 0, 1)
}

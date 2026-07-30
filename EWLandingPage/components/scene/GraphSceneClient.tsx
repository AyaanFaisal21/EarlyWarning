'use client'

import dynamic from 'next/dynamic'

/**
 * Client-only wrapper for the 3D scene.
 *
 * R3F's <Canvas> produces different markup on the server than on the client, which trips
 * React's hydration check ("some attributes of the server rendered HTML didn't match").
 * There is nothing to gain from server-rendering a WebGL canvas, so skip it entirely.
 *
 * The placeholder keeps the layout stable during the swap — a plain white panel, which is
 * what the scene resolves to anyway, so there is no visible flash.
 */
export const GraphSceneClient = dynamic(
  () => import('./GraphScene').then((m) => m.GraphScene),
  {
    ssr: false,
    loading: () => <div style={{ width: '100%', height: '100%', background: '#ffffff' }} />,
  }
)

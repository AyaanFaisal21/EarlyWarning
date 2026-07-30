'use client'

import { Grid } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useRef } from 'react'
import * as THREE from 'three'

import { remap } from '@/lib/useScrollProgress'
import { AnimatedBox } from './AnimatedBox'

// The centre cube is deliberately absent from this list — it is a fixed landmark, not a
// wanderer, because the whole scroll transition zooms into one of its faces. A moving
// target would make the camera chase it.
const POSITIONS: [number, number, number][] = [
  [-9, 0.5, -9],
  [-3, 0.5, -3],
  [3, 0.5, 3],
  [9, 0.5, 9],
  [-6, 0.5, 6],
  [6, 0.5, -6],
  [-12, 0.5, 0],
  [12, 0.5, 0],
  [0, 0.5, 12],
]

// Grid line colours at rest and at the end of the descent. The grid does not disappear —
// it darkens until it is indistinguishable from the black backdrop the tiles have already
// laid down, so the two surfaces merge instead of one cutting to the other.
const CELL_FROM = new THREE.Color('#4a4a4a')
const CELL_TO = new THREE.Color('#141414')
const SECTION_FROM = new THREE.Color('#6e6e6e')

/**
 * Drives the camera from scroll instead of OrbitControls.
 *
 * OrbitControls is removed deliberately — it owns the camera, so a scroll-driven dolly
 * fights it and the result judders. Scroll is the only input here.
 *
 * At rest the camera drifts slowly around the scene so the hero is alive before anyone
 * touches the wheel; the drift is scaled out as the dolly takes over.
 */
function CameraRig({ progress }: { progress: number }) {
  const { camera } = useThree()
  const target = useRef(new THREE.Vector3())

  useFrame((state) => {
    const t = remap(progress, 0, 0.12, 0, 1)

    // Idle drift accumulates without bound off elapsedTime, so by the time someone
    // scrolls the orbit angle can be several turns past where it started. Lerping that raw
    // value toward a fixed target made the camera unwind every one of those turns on the
    // way down — the "spins several times". Normalising the delta to [-PI, PI] caps the
    // approach at half a rotation however long the page has been sitting idle.
    const drift = state.clock.elapsedTime * 0.05 * (1 - t)
    const orbit = Math.PI / 4 + drift
    let delta = (Math.PI / 2 - orbit) % (Math.PI * 2)
    if (delta > Math.PI) delta -= Math.PI * 2
    if (delta < -Math.PI) delta += Math.PI * 2

    const angle = orbit + delta * t
    // Descend toward the grid plane rather than at any one object. There is no centre cube
    // any more — the destination is the surface itself, which darkens to black as we
    // arrive.
    const radius = THREE.MathUtils.lerp(42, 3.5, t)
    const height = THREE.MathUtils.lerp(30, 1.1, t)

    target.current.set(Math.cos(angle) * radius, height, Math.sin(angle) * radius)
    camera.position.lerp(target.current, 0.09)
    camera.lookAt(0, 0.4, 0)
  })

  return null
}

export function GraphScene({ progress }: { progress: number }) {
  // Fade the lines to black over the same window the tiles are settling in, so the 3D
  // surface and the 2D backdrop arrive at the same colour together.
  const k = remap(progress, 0.06, 0.12, 0, 1)
  const cell = CELL_FROM.clone().lerp(CELL_TO, k)
  const section = SECTION_FROM.clone().lerp(CELL_TO, k)

  return (
    <Canvas camera={{ position: [30, 30, 30], fov: 50, near: 0.01, far: 400 }} className="absolute inset-0">
      <CameraRig progress={progress} />

      {/* Ambient tuned for the grey stage: enough to separate cube faces, not so much
          that they wash out toward the background tone */}
      <ambientLight intensity={1.6} />
      <directionalLight position={[10, 18, 8]} intensity={1.1} />

      <Grid
        renderOrder={-1}
        position={[0, 0, 0]}
        infiniteGrid
        cellSize={1}
        cellThickness={0.5}
        sectionSize={3}
        sectionThickness={1}
        // inverted: dark lines on white, was light-on-black
        cellColor={cell}
        sectionColor={section}
        fadeDistance={70}
        fadeStrength={0.8}
      />

      {POSITIONS.map((position, i) => (
        <AnimatedBox key={i} initialPosition={position} intervalMs={900 + i * 60} />
      ))}
    </Canvas>
  )
}

'use client'

import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState } from 'react'
import * as THREE from 'three'

const STEP = 3
const BOUND = 15
// radius around the origin the wanderers must never enter — the centre cube lives there
const KEEP_CLEAR = 2

/**
 * A cube that hops between adjacent grid intersections.
 *
 * Inverted palette: dark faces with light edges on a white ground, so the cubes read as
 * solid objects sitting on the grid rather than glowing out of a dark void.
 */
export function AnimatedBox({
  initialPosition,
  intervalMs = 1000,
}: {
  initialPosition: [number, number, number]
  intervalMs?: number
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const current = useRef(new THREE.Vector3(...initialPosition))
  const [target, setTarget] = useState(() => new THREE.Vector3(...initialPosition))

  // Built once and shared by the mesh and its outline — rebuilding geometry every frame is
  // the usual cause of a creeping memory leak in R3F scenes.
  const geometry = useMemo(() => new THREE.BoxGeometry(1, 1, 1), [])
  const edges = useMemo(() => new THREE.EdgesGeometry(geometry), [geometry])

  useEffect(() => {
    const id = setInterval(() => {
      const dirs = [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ]
      // Try each direction in a random order and take the first that doesn't land on the
      // origin. The centre cube is the zoom target for the whole scroll transition — a
      // wanderer parking on top of it means the camera flies into a different cube than
      // the one it framed, and the face-to-background handoff visibly breaks.
      const shuffled = [...dirs].sort(() => Math.random() - 0.5)
      for (const [dx, dz] of shuffled) {
        const next = new THREE.Vector3(
          THREE.MathUtils.clamp(current.current.x + dx * STEP, -BOUND, BOUND),
          0.5,
          THREE.MathUtils.clamp(current.current.z + dz * STEP, -BOUND, BOUND)
        )
        if (Math.hypot(next.x, next.z) > KEEP_CLEAR) {
          setTarget(next)
          return
        }
      }
    }, intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])

  useFrame(() => {
    if (!meshRef.current) return
    current.current.lerp(target, 0.1)
    meshRef.current.position.copy(current.current)
  })

  useEffect(
    () => () => {
      geometry.dispose()
      edges.dispose()
    },
    [geometry, edges]
  )

  return (
    <mesh ref={meshRef} position={initialPosition} geometry={geometry}>
      <meshStandardMaterial color="#0e0e0e" roughness={0.8} metalness={0} />
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#f5f5f5" />
      </lineSegments>
    </mesh>
  )
}

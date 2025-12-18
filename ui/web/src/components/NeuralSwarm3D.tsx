import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Sphere } from '@react-three/drei'
import * as THREE from 'three'

// Agent node component
function AgentNode({ position, color, label: _label }: any) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01
      // Pulse effect
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1
      meshRef.current.scale.set(scale, scale, scale)
    }
  })

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[0.3, 32, 32]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          roughness={0.3}
          metalness={0.7}
        />
      </Sphere>
      {/* Connection lines would go here */}
    </group>
  )
}

// Main 3D scene
function Scene() {
  const agents = useMemo(() => [
    { position: [0, 0, 0], color: '#06b6d4', label: 'Orchestrator' },
    { position: [2, 1, 0], color: '#10b981', label: 'Bull' },
    { position: [2, -1, 0], color: '#ef4444', label: 'Bear' },
    { position: [-2, 1, 0], color: '#8b5cf6', label: 'Researcher' },
    { position: [-2, -1, 0], color: '#f59e0b', label: 'Analyzer' },
    { position: [0, 2, 0], color: '#ec4899', label: 'Risk' },
    { position: [0, -2, 0], color: '#14b8a6', label: 'Privacy' },
  ], [])

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#8b5cf6" />

      {agents.map((agent, i) => (
        <AgentNode key={i} {...agent} />
      ))}

      <OrbitControls
        enableZoom={true}
        enablePan={false}
        autoRotate
        autoRotateSpeed={0.5}
      />

      {/* Background grid */}
      <gridHelper args={[20, 20, '#ffffff20', '#ffffff10']} />
    </>
  )
}

export default function NeuralSwarm3D() {
  return (
    <div className="w-full h-full bg-gradient-to-br from-gray-900 to-purple-900/50">
      <Canvas camera={{ position: [5, 5, 5], fov: 60 }}>
        <Scene />
      </Canvas>
    </div>
  )
}

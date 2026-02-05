import { Cpu } from 'lucide-react'

export default function QuantumCircuit() {
  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
        <Cpu className="w-5 h-5 text-cyan-400" />
        <span>Quantum Circuit</span>
      </h3>

      <div className="aspect-video rounded-lg bg-gradient-to-br from-purple-900/50 to-cyan-900/50 flex items-center justify-center border border-white/10">
        <div className="text-center">
          <Cpu className="w-12 h-12 text-cyan-400 mx-auto mb-2 animate-pulse" />
          <p className="text-sm text-gray-400">Quantum circuit visualization</p>
          <p className="text-xs text-gray-500 mt-1">VQE optimization active</p>
        </div>
      </div>

      <div className="mt-4 space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-400">Backend</span>
          <span className="font-semibold">Aer Simulator</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Shots</span>
          <span className="font-semibold">1000</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Method</span>
          <span className="font-semibold">VQE</span>
        </div>
      </div>
    </div>
  )
}

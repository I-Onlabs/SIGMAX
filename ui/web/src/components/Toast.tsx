import { useEffect } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react'

interface ToastProps {
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  onClose: () => void
}

export default function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000)
    return () => clearTimeout(timer)
  }, [onClose])

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: AlertCircle,
  }

  const colors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-yellow-500',
    info: 'bg-blue-500',
  }

  const Icon = icons[type]

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center space-x-3 px-4 py-3 rounded-lg text-white shadow-lg ${colors[type]}`}>
      <Icon className="w-5 h-5" />
      <span className="flex-1">{message}</span>
      <button onClick={onClose} className="hover:opacity-75">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
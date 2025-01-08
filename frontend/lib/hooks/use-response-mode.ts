import { useState, useEffect } from 'react'
import { useToast } from "@/components/ui/use-toast"
import { Target, Zap, Sparkles } from 'lucide-react'

export type Mode = 'accurate' | 'interactive' | 'flexible'

export function useResponseMode() {
  const [mode, setMode] = useState<Mode>('interactive')
  const { toast } = useToast()

  useEffect(() => {
    fetchCurrentMode()
  }, [])

  const fetchCurrentMode = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/get-precision`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setMode(data.mode as Mode)
      }
    } catch (error) {
      console.error('Error fetching precision mode:', error)
    }
  }

  const handleModeChange = async (newMode: Mode) => {
    const token = localStorage.getItem('token')
    if (!token) {
      toast({
        title: "Authentication Error",
        description: "Please login again to change response modes.",
        variant: "destructive",
        duration: 3000,
      })
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/set-precision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ mode: newMode.toLowerCase() })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to change mode')
      }

      setMode(newMode)
      toast({
        title: `${newMode} Mode Activated`,
        description: modeDescriptions[newMode],
        duration: 3000,
      })
    } catch (error) {
      console.error('Error changing mode:', error)
      toast({
        title: "Mode Change Failed",
        description: error instanceof Error ? error.message : "Could not change response mode. Please try again.",
        variant: "destructive",
        duration: 4000,
      })
    }
  }

  return {
    mode,
    setMode,
    handleModeChange,
    fetchCurrentMode
  }
}

export const modeIcons = {
  accurate: Target,
  interactive: Zap,
  flexible: Sparkles,
}

export const modeDescriptions = {
  accurate: "Only uses information from provided documents. Best for factual queries about your documents.",
  interactive: "Primarily uses document information while allowing helpful supplementary knowledge. Good balance for most uses.",
  flexible: "Combines document knowledge with broader understanding. Best for exploratory discussions and complex topics.",
} 
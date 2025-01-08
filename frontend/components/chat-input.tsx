'use client'

import React from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRouter } from 'next/navigation'
import { useToast } from "@/components/ui/use-toast"

interface ChatInputProps {
  sessionId?: string | null
  onSubmit: (message: string) => Promise<void>
  placeholder?: string
  disabled?: boolean
}

export function ChatInput({ sessionId, onSubmit, placeholder = "Type your message...", disabled = false }: ChatInputProps) {
  const [input, setInput] = React.useState('')
  const [isProcessing, setIsProcessing] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isProcessing || disabled) return

    setIsProcessing(true)
    try {
      await onSubmit(input.trim())
      setInput('')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t">
      <div className="flex space-x-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          className="flex-1"
          disabled={disabled || isProcessing}
        />
        <Button 
          type="submit" 
          disabled={disabled || isProcessing || !input.trim()}
        >
          {isProcessing ? "Sending..." : "Send"}
        </Button>
      </div>
    </form>
  )
} 
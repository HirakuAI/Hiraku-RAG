'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/components/ui/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { ChevronDown, Zap, Target, Sparkles, Upload } from 'lucide-react'
import { ChatInput } from "@/components/chat-input"

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type Mode = 'accurate' | 'interactive' | 'flexible'

interface ChatInterfaceProps {
  sessionId: string | null
  chatHistory?: Message[]
}

const modeIcons = {
  accurate: Target,
  interactive: Zap,
  flexible: Sparkles,
}

const modeDescriptions = {
  accurate: "Only uses information from provided documents. Best for factual queries about your documents.",
  interactive: "Primarily uses document information while allowing helpful supplementary knowledge. Good balance for most uses.",
  flexible: "Combines document knowledge with broader understanding. Best for exploratory discussions and complex topics.",
}

const modeToastMessages = {
  accurate: {
    title: "Accurate Mode Activated",
    description: "Responses will strictly use document information only. Best for factual queries."
  },
  interactive: {
    title: "Interactive Mode Activated",
    description: "Responses will balance document information with helpful context. Good for general use."
  },
  flexible: {
    title: "Flexible Mode Activated",
    description: "Responses will combine document knowledge with broader understanding. Best for exploration."
  }
}

export function ChatInterface({ sessionId, chatHistory = [] }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(chatHistory)
  const [mode, setMode] = useState<Mode>('interactive')
  const [uploading, setUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  // Update messages when chat history changes
  useEffect(() => {
    setMessages(chatHistory)
  }, [chatHistory])

  // Memoize handleQuestion to prevent unnecessary re-renders
  const handleQuestion = React.useCallback(async (question: string) => {
    console.log('handleQuestion called with:', question)
    if (!sessionId) return

    const token = localStorage.getItem('token')
    if (!token) {
      toast({
        title: "Error",
        description: "Authentication required. Please login again.",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: parseInt(sessionId, 10),
          question,
          mode: mode.toLowerCase()
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to get response')
      }

      const data = await response.json()
      // Fetch the updated chat history after the response
      const historyResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/chat-history?session_id=${sessionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      
      if (!historyResponse.ok) {
        throw new Error('Failed to update chat history')
      }
      
      const historyData = await historyResponse.json()
      setMessages(historyData.history)
    } catch (error) {
      console.error('Error getting response:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get response. Please try again.",
        variant: "destructive"
      })
      // Only add error message to local state
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I apologize, but I encountered an error processing your request. Please try again."
      }])
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId, mode, toast])

  useEffect(() => {
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

    fetchCurrentMode()
  }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const token = localStorage.getItem('token')
    if (!token) {
      toast({
        title: "Error",
        description: "Authentication required. Please login again.",
        variant: "destructive"
      })
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to upload file')
      }

      const data = await response.json()
      toast({
        title: "Success",
        description: `File ${file.name} uploaded successfully.`,
      })
      setMessages(prev => [...prev, 
        { role: 'user', content: `Uploaded file: ${file.name}` },
        { role: 'assistant', content: "I've processed the uploaded file. You can now ask questions about its contents." }
      ])
    } catch (error) {
      console.error('Error uploading file:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload file.",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
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
        title: modeToastMessages[newMode].title,
        description: modeToastMessages[newMode].description,
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

  const ModeIcon = modeIcons[mode]

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-4 ${
              message.role === 'user' ? 'text-right' : 'text-left'
            }`}
          >
            <div
              className={`inline-block p-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="mb-4 text-left">
            <div className="inline-block p-2 rounded-lg bg-muted">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
      </ScrollArea>
      <ChatInput 
        sessionId={sessionId} 
        onSubmit={handleQuestion}
        disabled={isProcessing}
      />
    </div>
  )
}


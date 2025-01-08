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

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type Mode = 'accurate' | 'interactive' | 'flexible'

interface ChatInterfaceProps {
  sessionId: string | null
  initialQuestion: string | null
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

export function ChatInterface({ sessionId, initialQuestion, chatHistory = [] }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(chatHistory)
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<Mode>('interactive')
  const [uploading, setUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [initialQuestionProcessed, setInitialQuestionProcessed] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  // Reset messages when session changes
  useEffect(() => {
    setMessages(chatHistory)
    setInitialQuestionProcessed(false)
  }, [sessionId, chatHistory])

  useEffect(() => {
    console.log('Effect triggered:', { sessionId, initialQuestion, initialQuestionProcessed, messagesLength: messages.length })
    if (sessionId && initialQuestion && !initialQuestionProcessed) {
      console.log('Processing initial question:', initialQuestion)
      setInitialQuestionProcessed(true)
      handleQuestion(initialQuestion)
    }
  }, [sessionId, initialQuestion, initialQuestionProcessed])

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

  const handleQuestion = async (question: string) => {
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

    const newMessages = [...messages, { role: 'user' as const, content: question }]
    setMessages(newMessages)
    setInput('')
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
      setMessages([...newMessages, { role: 'assistant' as const, content: data.answer }])
    } catch (error) {
      console.error('Error getting response:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get response. Please try again.",
        variant: "destructive"
      })
      // Add error message to chat
      setMessages([...newMessages, { 
        role: 'assistant', 
        content: "I apologize, but I encountered an error processing your request. Please try again."
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isProcessing) return
    await handleQuestion(input.trim())
  }

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
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" className="w-14 px-0 flex-shrink-0">
                      <div className="flex items-center">
                        <ModeIcon className="h-4 w-4" />
                        <ChevronDown className="h-3 w-3 ml-0.5" />
                      </div>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    {(Object.keys(modeDescriptions) as Mode[]).map((m) => (
                      <DropdownMenuItem key={m} onSelect={() => handleModeChange(m)}>
                        <div className="flex items-center">
                          {React.createElement(modeIcons[m], { className: "h-4 w-4 mr-2" })}
                          <span className="capitalize">{m}</span>
                        </div>
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TooltipTrigger>
              <TooltipContent side="top" align="start" className="max-w-xs">
                <p className="font-semibold capitalize">{mode} Mode</p>
                <p className="text-sm">{modeDescriptions[mode]}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1"
          />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="flex-shrink-0"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Upload className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Upload a file</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileUpload}
          />
          <Button type="submit" className="flex-shrink-0">Send</Button>
        </div>
      </form>
    </div>
  )
}


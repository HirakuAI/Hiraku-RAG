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
import { Upload } from 'lucide-react'
import { useResponseMode, modeIcons, modeDescriptions, type Mode } from "@/lib/hooks/use-response-mode"

type Message = {
  role: 'user' | 'assistant'
  content: string
}

interface ChatInterfaceProps {
  sessionId: string | null
  chatHistory?: Message[]
}

export function ChatInterface({ sessionId, chatHistory = [] }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(chatHistory)
  const { mode, handleModeChange } = useResponseMode()
  const [uploading, setUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const [input, setInput] = useState('')

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
    // Add an empty assistant message that we'll stream into
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          question,
          mode: mode.toLowerCase()
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to get response')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response stream available')

      let currentContent = ''
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Decode the chunk
        const chunk = decoder.decode(value)
        
        // Process each SSE message
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6) // Remove 'data: ' prefix
            currentContent += data
            
            // Update the last message with the new content
            setMessages(prev => {
              const newMessages = [...prev]
              newMessages[newMessages.length - 1] = {
                role: 'assistant',
                content: currentContent
              }
              return newMessages
            })
          }
        }
      }

      // After streaming is complete, update chat history
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
      // Update the empty assistant message with an error
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: "I apologize, but I encountered an error processing your request. Please try again."
        }
        return newMessages
      })
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId, mode, toast])

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

  const ModeIcon = modeIcons[mode]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isProcessing) return
    
    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    
    try {
      await handleQuestion(userMessage)
    } catch (error) {
      console.error('Error submitting question:', error)
    }
  }

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
            <div className="text-sm text-muted-foreground italic">
              <span className="inline-block animate-pulse">·</span>
              <span className="inline-block animate-pulse delay-150">·</span>
              <span className="inline-block animate-pulse delay-300">·</span>
            </div>
          </div>
        )}
      </ScrollArea>
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1"
            disabled={isProcessing}
          />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      type="button" 
                      variant="ghost" 
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-foreground"
                    >
                      <ModeIcon className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    {(Object.keys(modeIcons) as Mode[]).map((m) => {
                      const Icon = modeIcons[m]
                      return (
                        <DropdownMenuItem
                          key={m}
                          onClick={() => handleModeChange(m)}
                          className="flex items-center gap-2"
                        >
                          <Icon className="h-4 w-4" />
                          <div className="flex flex-col">
                            <span className="capitalize">{m}</span>
                            <span className="text-xs text-muted-foreground">
                              {modeDescriptions[m]}
                            </span>
                          </div>
                        </DropdownMenuItem>
                      )
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TooltipTrigger>
              <TooltipContent>
                <p className="capitalize">{mode} mode</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-foreground"
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
          <Button 
            type="submit" 
            disabled={isProcessing || !input.trim()}
          >
            {isProcessing ? "Sending..." : "Send"}
          </Button>
        </div>
      </form>
    </div>
  )
}


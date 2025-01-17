'use client'

import React, { useState, useRef, useEffect } from 'react'
import MarkdownRenderer from 'react-markdown-renderer'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/components/ui/use-toast"
import { GlowingTextarea } from '@/components/ui/glowing-textarea'
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
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Update messages when chat history changes
  useEffect(() => {
    setMessages(chatHistory)
  }, [chatHistory])

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }

  useEffect(() => {
    adjustTextareaHeight()
  }, [input])

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
    const files = e.target.files
    if (!files || files.length === 0) return

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
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

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
        throw new Error(errorData.error || 'Failed to upload files')
      }

      const data = await response.json()
      toast({
        title: "Success",
        description: data.message,
      })
      setMessages(prev => [...prev, 
        { role: 'user', content: `Uploaded files: ${Array.from(files).map(f => f.name).join(', ')}` },
        { role: 'assistant', content: "I've processed the uploaded files. You can now ask questions about their contents." }
      ])
    } catch (error) {
      console.error('Error uploading files:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload files.",
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const formEvent = { preventDefault: () => {} } as React.FormEvent
      handleSubmit(formEvent)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 pb-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`group relative mb-4 flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`flex max-w-[85%] md:max-w-[75%] ${
                    message.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  <div
                    className={`overflow-hidden rounded-lg px-3 py-2 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <div className="prose prose-sm dark:prose-invert max-w-none [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
                      <MarkdownRenderer markdown={message.content} />
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="mb-4 flex justify-start">
                <div className="text-sm text-muted-foreground italic">
                  Thinking...
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
      <div className="flex-none w-full border-t bg-background shadow-[0_-2px_10px_rgba(0,0,0,0.1)]">
        <form onSubmit={handleSubmit} className="flex gap-2 p-4">
          <div className="relative flex-1">
            <GlowingTextarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message... (Press Shift + Enter for new line)"
              disabled={isProcessing || !sessionId}
              isProcessing={isProcessing}
              className="min-h-[44px] max-h-[200px] overflow-y-auto py-3 pr-12 transition-height duration-200"
              rows={1}
            />
            <div className="absolute right-3 bottom-[10px] text-xs text-muted-foreground">
              {input.length > 0 && <span>⏎ to send</span>}
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="submit"
                  disabled={isProcessing || !sessionId || !input.trim()}
                >
                  Send
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Send message (Enter)
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileUpload}
            multiple
          />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading || !sessionId}
                >
                  <Upload className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Upload file
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <DropdownMenu>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" disabled={!sessionId}>
                      <ModeIcon className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                </TooltipTrigger>
                <TooltipContent>
                  Change response mode
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <DropdownMenuContent align="end">
              {Object.entries(modeIcons).map(([key, Icon]) => (
                <DropdownMenuItem
                  key={key}
                  onClick={() => handleModeChange(key as Mode)}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  <span>{key}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {modeDescriptions[key as Mode]}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </form>
      </div>
    </div>
  )
}
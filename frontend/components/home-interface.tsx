'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Upload, Target, Zap, Sparkles, ArrowRight } from 'lucide-react'
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
import { useResponseMode, modeIcons, modeDescriptions, type Mode } from "@/lib/hooks/use-response-mode"

interface HomeInterfaceProps {
  onQuestionSubmit: (question: string) => Promise<void>
}

export function HomeInterface({ onQuestionSubmit }: HomeInterfaceProps) {
  const [input, setInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const { mode, handleModeChange } = useResponseMode()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { toast } = useToast()

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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const formEvent = { preventDefault: () => {} } as React.FormEvent
      handleSubmit(formEvent)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    try {
      await onQuestionSubmit(input.trim())
      setInput('')
    } finally {
      setIsSubmitting(false)
    }
  }

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

  return (
    <div className="flex flex-col items-center justify-center flex-1 p-4">
      <div className="w-full max-w-2xl mx-auto">
        <h1 className="text-4xl font-semibold text-center mb-6">
          What do you want to know?
        </h1>
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything... (Press Shift + Enter for new line)"
              className="w-full pr-32 min-h-[48px] max-h-[200px] overflow-y-auto resize-none py-3 bg-background transition-height duration-200"
              rows={1}
            />
            <div className="absolute right-1.5 top-[10px] flex items-center gap-1">
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
                multiple
              />
              <Button 
                type="submit" 
                size="icon"
                className="h-8 w-8"
                disabled={!input.trim() || isSubmitting}
              >
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}


'use client'

import { useState, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Upload, Target, Zap, Sparkles, ArrowRight, ChevronDown } from 'lucide-react'
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

type Mode = 'accurate' | 'interactive' | 'flexible'

const modeIcons = {
  accurate: Target,
  interactive: Zap,
  flexible: Sparkles,
}

const modeDescriptions = {
  accurate: "Only uses information from provided documents",
  interactive: "Balances document info with helpful knowledge",
  flexible: "Combines documents with broader understanding",
}

interface HomeInterfaceProps {
  onQuestionSubmit: (question: string) => Promise<void>
}

export function HomeInterface({ onQuestionSubmit }: HomeInterfaceProps) {
  const [input, setInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [mode, setMode] = useState<Mode>('interactive')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    try {
      await onQuestionSubmit(input.trim())
    } finally {
      setIsSubmitting(false)
    }
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

      toast({
        title: "Success",
        description: `File ${file.name} uploaded successfully.`,
      })
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

  return (
    <div className="flex flex-col items-center justify-center flex-1 p-4">
      <div className="w-full max-w-2xl mx-auto">
        <h1 className="text-4xl font-semibold text-center mb-6">
          What do you want to know?
        </h1>
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              className="w-full pr-32 h-12 bg-background"
            />
            <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
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


'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Paperclip, ArrowRight, Zap, Target, Sparkles } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type Mode = 'accurate' | 'interactive' | 'flexible'

interface HomeInterfaceProps {
  onQuestionSubmit: (question: string) => Promise<void>
}

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

export function HomeInterface({ onQuestionSubmit }: HomeInterfaceProps) {
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<Mode>('interactive')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    try {
      await onQuestionSubmit(input.trim())
    } catch (error) {
      console.error('Error submitting question:', error)
      // You might want to show an error toast here
    } finally {
      setIsSubmitting(false)
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
                              onClick={() => setMode(m)}
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
                    >
                      <Paperclip className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Attach files</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Button 
                type="submit" 
                size="icon"
                className="h-8 w-8"
                disabled={!input.trim()}
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


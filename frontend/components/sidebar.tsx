'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, Home, Map, FolderOpen, MessageCircleMore, User, Settings, GripVertical, Command, BookOpen, Trash2, ChevronUp } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/lib/auth-context"
import { useToast } from "@/components/ui/use-toast"
import { useRouter } from 'next/navigation'

const MIN_SIDEBAR_WIDTH = 240
const MAX_SIDEBAR_WIDTH = 400

interface SidebarProps {
  initialSessionId?: string
  onViewChange?: (view: 'home' | 'chat', sessionId?: string) => void
}

type Model = 'Llama 3.1 70B' | 'GPT-4o' | 'Claude 3.5 Sonnet' | 'Unsenser Model' | string

interface ChatSession {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export function Sidebar({ initialSessionId, onViewChange }: SidebarProps) {
  const router = useRouter()
  const [isResizing, setIsResizing] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(280)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [chatToDelete, setChatToDelete] = useState<number | null>(null)
  const [selectedModel, setSelectedModel] = useState<Model>('Llama 3.1 70B')
  const [isCustomModelDialogOpen, setIsCustomModelDialogOpen] = useState(false)
  const [customModelName, setCustomModelName] = useState('')
  const [customModelAPI, setCustomModelAPI] = useState('')
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const { user, logout } = useAuth()
  const { toast } = useToast()

  const startResizing = useCallback(() => {
    setIsResizing(true)
  }, [])

  const stopResizing = useCallback(() => {
    setIsResizing(false)
  }, [])

  const resize = useCallback(
    (mouseMoveEvent: MouseEvent) => {
      if (isResizing) {
        const newWidth = mouseMoveEvent.clientX
        if (newWidth >= MIN_SIDEBAR_WIDTH && newWidth <= MAX_SIDEBAR_WIDTH) {
          setSidebarWidth(newWidth)
        }
      }
    },
    [isResizing]
  )

  const fetchChatSessions = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat-sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch chat sessions')
      }

      const data = await response.json()
      setChatSessions(data.sessions)
    } catch (error) {
      console.error('Error fetching chat sessions:', error)
      toast({
        title: "Error",
        description: "Failed to load chat history",
        variant: "destructive"
      })
    }
  }

  useEffect(() => {
    fetchChatSessions()

    // Listen for chat session updates
    const handleSessionCreated = () => {
      fetchChatSessions()
    }

    window.addEventListener('chatSessionCreated', handleSessionCreated)

    return () => {
      window.removeEventListener('chatSessionCreated', handleSessionCreated)
    }
  }, [])

  const handleDeleteClick = async (sessionId: number) => {
    setChatToDelete(sessionId)
    setIsDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (chatToDelete === null) return

    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat-sessions/${chatToDelete}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to delete chat session')
      }

      // Remove the deleted session from state
      setChatSessions(prev => prev.filter(session => session.id !== chatToDelete))
      toast({
        title: "Success",
        description: "Chat session deleted successfully"
      })
    } catch (error) {
      console.error('Error deleting chat session:', error)
      toast({
        title: "Error",
        description: "Failed to delete chat session",
        variant: "destructive"
      })
    }

    setIsDeleteDialogOpen(false)
    setChatToDelete(null)
  }

  const handleAddCustomModel = () => {
    if (customModelName && customModelAPI) {
      setSelectedModel(customModelName)
      setIsCustomModelDialogOpen(false)
      setCustomModelName('')
      setCustomModelAPI('')
    }
  }

  const navigateToChat = useCallback((sessionId: string) => {
    if (onViewChange) {
      onViewChange('chat', sessionId)
    } else {
      router.push(`/chat/${sessionId}`)
    }
  }, [onViewChange, router])

  const navigateToHome = useCallback(() => {
    if (onViewChange) {
      onViewChange('home')
    } else {
      router.push('/')
    }
  }, [onViewChange, router])

  useEffect(() => {
    window.addEventListener('mousemove', resize)
    window.addEventListener('mouseup', stopResizing)
    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
    }
  }, [resize, stopResizing])

  return (
    <>
      <div
        className="relative flex flex-col h-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-r"
        style={{ width: sidebarWidth }}
      >
        {/* Logo Section */}
        <div className="p-4">
          <div className="flex items-center space-x-2">
            <div className="bg-primary text-primary-foreground w-8 h-8 rounded-lg flex items-center justify-center font-bold text-lg">
              H
            </div>
            <span className="font-semibold text-xl">Hiraku</span>
          </div>
        </div>

        {/* Search Input */}
        <div className="px-4 mb-4">
          <div className="relative">
            <Input 
              placeholder="Type to ask" 
              className="pl-9 pr-12 bg-muted/50 border-0 focus-visible:ring-1"
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                <span className="text-xs">⌘</span>K
              </kbd>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="px-3">
          <nav className="space-y-1">
            <Button
              variant="ghost" 
              className="w-full justify-start text-base font-normal"
              onClick={navigateToHome}
            >
              <Home className="mr-2 h-5 w-5" />
              Home
            </Button>
            <Button variant="ghost" className="w-full justify-start text-base font-normal">
              <Map className="mr-2 h-5 w-5" />
              Knowledge map
            </Button>
            <Button variant="ghost" className="w-full justify-start text-base font-normal">
              <BookOpen className="mr-2 h-5 w-5" />
              Library
            </Button>
          </nav>
        </div>

        {/* Recent Chats */}
        <ScrollArea className="flex-1 px-3">
          <div className="py-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-2 px-2">History</h3>
            <div className="space-y-1">
              {chatSessions.map((session) => (
                <div key={session.id} className="group relative">
                  <Button
                    variant="ghost" 
                    className="w-full justify-start text-sm font-normal text-muted-foreground"
                    onClick={() => navigateToChat(session.id.toString())}
                  >
                    {session.title}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteClick(session.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </ScrollArea>

        {/* Model Selection */}
        <div className="px-4 py-2 border-t bg-background/95">
          <Dialog open={isCustomModelDialogOpen} onOpenChange={setIsCustomModelDialogOpen}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="outline" 
                  className="w-full justify-between h-9 px-3"
                  size="sm"
                >
                  <span className="text-sm font-medium">{selectedModel}</span>
                  <ChevronUp className="h-4 w-4 ml-2 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-[--radix-dropdown-menu-trigger-width]">
                <DropdownMenuItem onSelect={() => setSelectedModel('Llama 3.1 70B')}>
                  Llama 3.1 70B
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setSelectedModel('GPT-4o')}>
                  GPT-4o
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setSelectedModel('Claude 3.5 Sonnet')}>
                  Claude 3.5 Sonnet
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setSelectedModel('Unsenser Model')}>
                  Unsenser Model
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DialogTrigger asChild>
                  <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                    Add custom model
                  </DropdownMenuItem>
                </DialogTrigger>
              </DropdownMenuContent>
            </DropdownMenu>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Add Custom Model</DialogTitle>
                <DialogDescription>
                  Enter the details of your custom model.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="name" className="text-right">
                    Name
                  </Label>
                  <Input
                    id="name"
                    value={customModelName}
                    onChange={(e) => setCustomModelName(e.target.value)}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="api" className="text-right">
                    API Endpoint
                  </Label>
                  <Input
                    id="api"
                    value={customModelAPI}
                    onChange={(e) => setCustomModelAPI(e.target.value)}
                    className="col-span-3"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCustomModelDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddCustomModel}>Add Model</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* User Section */}
        <div className="p-4 border-t bg-background/95">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src="/placeholder-avatar.jpg" />
                <AvatarFallback>{user?.username?.[0]?.toUpperCase() || <User className="h-4 w-4" />}</AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium">{user?.username || 'Guest'}</span>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600" onClick={logout}>
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Resize Handle */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-primary/10 transition-colors flex items-center justify-center"
          onMouseDown={startResizing}
        >
          <div className="h-16 w-1 flex items-center justify-center">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this chat history? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}


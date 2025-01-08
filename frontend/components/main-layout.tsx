'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { HomeInterface } from "./home-interface"
import { ChatInterface } from "./chat-interface"
import { Header } from "./header"
import { useAuth } from "@/lib/auth-context"
import { useToast } from "@/components/ui/use-toast"

type View = 'home' | 'chat'

interface MainLayoutProps {
  initialSessionId?: string
  initialQuestion?: string | null
}

export function MainLayout({ initialSessionId, initialQuestion: propInitialQuestion }: MainLayoutProps) {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const { toast } = useToast()
  const [currentView, setCurrentView] = useState<View>(initialSessionId ? 'chat' : 'home')
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null)
  const [initialQuestion, setInitialQuestion] = useState<string | null>(propInitialQuestion || null)
  const [chatHistory, setChatHistory] = useState<any[]>([])

  useEffect(() => {
    if (initialSessionId && propInitialQuestion) {
      setInitialQuestion(propInitialQuestion)
    }
  }, [initialSessionId, propInitialQuestion])

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
  }, [isAuthenticated, router])

  useEffect(() => {
    if (initialSessionId) {
      loadChatSession(initialSessionId)
    }
  }, [initialSessionId])

  const loadChatSession = async (sessionId: string) => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat-history?session_id=${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to load chat history')
      }

      const data = await response.json()
      setCurrentSessionId(sessionId)
      setChatHistory(data.history || [])
    } catch (error) {
      console.error('Error loading chat session:', error)
      toast({
        title: "Error",
        description: "Failed to load chat session",
        variant: "destructive"
      })
    }
  }

  const createNewChatSession = async (question: string) => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return null
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat-sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          title: question.length > 30 
            ? question.substring(0, 30) + '...' 
            : question 
        })
      })

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login')
          return null
        }
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create chat session')
      }

      const data = await response.json()
      return data.session_id.toString()
    } catch (error) {
      console.error('Error creating chat session:', error)
      toast({
        title: "Error",
        description: "Failed to create new chat session. Please try again.",
        variant: "destructive",
      })
      return null
    }
  }

  const handleQuestionSubmit = async (question: string) => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    const sessionId = await createNewChatSession(question)
    if (!sessionId) return

    try {
      // Send the initial question first
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: parseInt(sessionId, 10),
          question,
          mode: 'interactive'
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send initial question')
      }

      // Then navigate to the chat interface
      router.push(`/chat/${sessionId}`)
    } catch (error) {
      console.error('Error sending initial question:', error)
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive"
      })
    }
  }

  // If not authenticated, return null (redirect will happen in useEffect)
  if (!isAuthenticated) {
    return null
  }

  return (
    <main className="flex-1 flex flex-col overflow-hidden" data-main-layout>
      <Header title={currentView === 'home' ? 'Home' : 'Chat'} />
      {currentView === 'home' ? (
        <HomeInterface onQuestionSubmit={handleQuestionSubmit} />
      ) : (
        <ChatInterface 
          sessionId={currentSessionId} 
          chatHistory={chatHistory}
        />
      )}
    </main>
  )
}


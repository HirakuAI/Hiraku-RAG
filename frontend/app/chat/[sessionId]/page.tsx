'use client'

import { useSearchParams } from 'next/navigation'
import { MainLayout } from "@/components/main-layout"
import { Sidebar } from "@/components/sidebar"

export default function ChatPage({ params }: { params: { sessionId: string } }) {
  const searchParams = useSearchParams()
  const initialQuestion = searchParams.get('initial')

  return (
    <div className="flex h-svh">
      <Sidebar initialSessionId={params.sessionId} />
      <MainLayout 
        initialSessionId={params.sessionId} 
        initialQuestion={initialQuestion}
      />
    </div>
  )
} 
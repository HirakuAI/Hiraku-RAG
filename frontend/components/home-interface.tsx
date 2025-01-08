'use client'

import { ChatInput } from "@/components/chat-input"

interface HomeInterfaceProps {
  onQuestionSubmit: (question: string) => Promise<void>
}

export function HomeInterface({ onQuestionSubmit }: HomeInterfaceProps) {
  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full space-y-4">
          <h1 className="text-4xl font-bold text-center">Welcome to Hiraku</h1>
          <p className="text-center text-muted-foreground">
            Ask me anything about your documents or start a new conversation.
          </p>
        </div>
      </div>
      <ChatInput 
        onSubmit={onQuestionSubmit}
        placeholder="Ask a question..."
      />
    </div>
  )
}


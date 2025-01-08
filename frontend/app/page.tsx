'use client'

import { MainLayout } from "@/components/main-layout"
import { Sidebar } from "@/components/sidebar"

export default function Home() {
  return (
    <div className="flex h-svh">
      <Sidebar onViewChange={(view, sessionId) => {
        // Dispatch view change event to MainLayout
        const mainLayout = document.querySelector('[data-main-layout]')
        if (mainLayout) {
          mainLayout.dispatchEvent(
            new CustomEvent('viewChange', { 
              detail: { 
                view,
                sessionId 
              } 
            })
          )
        }
      }} />
      <MainLayout />
    </div>
  )
}


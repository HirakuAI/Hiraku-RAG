'use client'

import { MainLayout } from "@/components/main-layout"
import { Sidebar } from "@/components/sidebar"

export default function Home() {
  return (
    <div className="flex h-svh">
      <Sidebar />
      <MainLayout />
    </div>
  )
}


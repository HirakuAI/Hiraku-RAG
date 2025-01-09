'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/components/ui/use-toast"

export function FileUpload() {
  const [files, setFiles] = useState<FileList | null>(null)
  const { toast } = useToast()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(e.target.files)
    }
  }

  const handleUpload = async () => {
    if (!files || files.length === 0) return

    const formData = new FormData()
    Array.from(files).forEach((file) => {
      formData.append('files', file)
    })

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      })

      if (!response.ok) throw new Error('Failed to upload files')

      toast({
        title: "Success",
        description: `${files.length} file(s) uploaded successfully.`,
      })
      
      // Clear the file input after successful upload
      setFiles(null)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload files.",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-2">
      <Input 
        type="file" 
        onChange={handleFileChange} 
        multiple 
        value=""
      />
      <Button onClick={handleUpload} disabled={!files || files.length === 0} className="w-full">
        Upload {files ? `(${files.length} file${files.length !== 1 ? 's' : ''})` : ''}
      </Button>
    </div>
  )
}


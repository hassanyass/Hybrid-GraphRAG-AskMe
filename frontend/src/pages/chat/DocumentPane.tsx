import { useState, useEffect } from 'react'
import { FileText, Loader2 } from 'lucide-react'
import { apiClient } from '@/api/client'

interface DocumentPaneProps {
  documentId: string | null
}

export function DocumentPane({ documentId }: DocumentPaneProps) {
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!documentId) {
      setUrl(null)
      return
    }

    const fetchUrl = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await apiClient.get<{ url: string }>(`/documents/${documentId}/download`)
        setUrl(response.data.url)
      } catch (err) {
        setError('Failed to load document preview.')
      } finally {
        setLoading(false)
      }
    }

    fetchUrl()
  }, [documentId])

  if (!documentId) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-neutral-dark bg-neutral-light/5">
        <FileText className="mb-4 h-12 w-12 opacity-20" />
        <p className="text-sm font-medium text-foreground">No Document Selected</p>
        <p className="mt-1 text-xs">Click on a citation in the chat to view the source document.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-neutral-light/5">
        <Loader2 className="h-8 w-8 animate-spin text-accent" />
        <p className="mt-4 text-sm text-neutral-dark">Loading document preview...</p>
      </div>
    )
  }

  if (error || !url) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center p-8 bg-neutral-light/5">
        <p className="text-sm text-red-500 font-medium">{error || 'Could not load document'}</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full bg-neutral-100 flex flex-col">
      <div className="p-2 bg-white border-b border-border text-xs text-neutral-dark font-medium flex justify-between items-center">
        <span>Document Preview</span>
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">Open in new tab</a>
      </div>
      <iframe 
        src={`${url}#toolbar=0&navpanes=0`} 
        className="flex-1 w-full border-none"
        title="Document Preview"
      />
    </div>
  )
}

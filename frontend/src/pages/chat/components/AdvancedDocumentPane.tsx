import { useState, useEffect, useMemo } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Loader2, AlertCircle, ZoomIn, ZoomOut, Search } from 'lucide-react'
import { DocumentService } from '@/services/DocumentService'
import { Button } from '@/components/ui/button'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface AdvancedDocumentPaneProps {
  documentId: string | null
  highlightText?: string
  initialPage?: number
}

export function AdvancedDocumentPane({ documentId, highlightText, initialPage }: AdvancedDocumentPaneProps) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [numPages, setNumPages] = useState<number | null>(null)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState(1.0)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (initialPage) setPageNumber(initialPage)
  }, [initialPage])

  useEffect(() => {
    if (!documentId) return
    let mounted = true
    setIsLoading(true)
    setError(null)

    DocumentService.getDocumentUrl(documentId)
      .then(fetchedUrl => {
        if (mounted) setUrl(fetchedUrl)
      })
      .catch(err => {
        console.error(err)
        if (mounted) setError('Failed to load document preview.')
      })
      .finally(() => {
        if (mounted) setIsLoading(false)
      })

    return () => { mounted = false }
  }, [documentId])

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  const textRenderer = useMemo(() => {
    if (!highlightText) return undefined
    
    return ({ str }: { str: string }) => {
      // Very basic text highlighter for react-pdf TextLayer
      if (!str || !highlightText) return str
      const index = str.toLowerCase().indexOf(highlightText.toLowerCase())
      if (index === -1) return str
      
      return (
        <span className="bg-accent/30 rounded px-0.5">
          {str}
        </span>
      )
    }
  }, [highlightText])

  if (!documentId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-neutral-400 p-8 text-center bg-[#F8FAFC]">
        <Search className="w-12 h-12 mb-4 text-neutral-300" />
        <h3 className="text-sm font-bold text-neutral-dark mb-1">No document selected</h3>
        <p className="text-xs">Select a document from the left navigation or click a citation in the chat to view it here.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-[#F8FAFC]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-white shadow-sm shrink-0">
        <div className="flex items-center gap-2">
           <Button variant="outline" size="sm" onClick={() => setPageNumber(p => Math.max(1, p - 1))} disabled={pageNumber <= 1}>Prev</Button>
           <span className="text-xs font-semibold text-neutral-dark min-w-[60px] text-center">
             {pageNumber} / {numPages || '?'}
           </span>
           <Button variant="outline" size="sm" onClick={() => setPageNumber(p => Math.min(numPages || p, p + 1))} disabled={!numPages || pageNumber >= numPages}>Next</Button>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.max(0.5, s - 0.2))}><ZoomOut className="w-4 h-4 text-neutral-dark" /></Button>
          <span className="text-xs font-medium text-neutral-dark w-12 text-center">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.min(2.5, s + 0.2))}><ZoomIn className="w-4 h-4 text-neutral-dark" /></Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto relative p-4 flex justify-center bg-neutral-200/50">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-10">
            <Loader2 className="w-6 h-6 animate-spin text-accent" />
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-red-500 gap-2 bg-white z-10 p-8 text-center">
             <AlertCircle className="w-8 h-8" />
             <span className="text-sm font-bold">{error}</span>
             <Button variant="outline" onClick={() => window.location.reload()} className="mt-4">Reload Workspace</Button>
          </div>
        )}

        {url && (
          <div className="bg-white shadow-lg border border-border">
            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<div className="p-8 text-sm text-neutral-400">Loading PDF...</div>}
            >
              <Page 
                pageNumber={pageNumber} 
                scale={scale} 
                renderTextLayer={true}
                renderAnnotationLayer={true}
                customTextRenderer={highlightText ? (textRenderer as any) : undefined}
                loading={<div className="w-full max-w-full aspect-[3/4] bg-white animate-pulse" />}
              />
            </Document>
          </div>
        )}
      </div>
    </div>
  )
}

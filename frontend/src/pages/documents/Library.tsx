import { useState } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Search, Plus, Trash2, FileText, AlertCircle, Loader2 } from 'lucide-react'
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments'

export function Library() {
  const { data: documents, isLoading, error } = useDocuments()
  const deleteMutation = useDeleteDocument()
  const [searchQuery, setSearchQuery] = useState('')

  const filteredDocs = documents?.filter(doc => 
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-6 text-red-700">
        <div className="flex items-center gap-3 mb-2">
          <AlertCircle className="h-5 w-5" />
          <h3 className="font-semibold text-lg">Knowledge Sync Error</h3>
        </div>
        <p>Failed to retrieve synced documents from the server.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl animate-in fade-in duration-500">
      <div className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Knowledge Sources</h1>
          <p className="mt-1 text-neutral-dark">Manage the documents synced to your active intelligence layer.</p>
        </div>
        <Link 
          to="/documents/upload" 
          className="flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-primary hover:bg-accent-hover transition-colors"
        >
          <Plus className="h-4 w-4" />
          Teach ASKME
        </Link>
      </div>

      <div className="mb-6 flex items-center">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-dark" />
          <input 
            type="text"
            placeholder="Search knowledge sources..." 
            className="w-full rounded border border-border bg-white pl-9 pr-4 py-2 text-sm text-foreground focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="rounded border border-border bg-white">
        {isLoading ? (
          <div className="divide-y divide-border">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between p-4 animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded bg-neutral-light/50"></div>
                  <div className="space-y-2">
                    <div className="h-4 w-48 rounded bg-neutral-light"></div>
                    <div className="h-3 w-24 rounded bg-neutral-light/50"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-neutral-light/50">
              <FileText className="h-6 w-6 text-neutral-dark" />
            </div>
            <p className="text-base font-medium text-foreground">No sources found</p>
            <p className="mt-1 text-sm text-neutral-dark">Add documents to expand your knowledge graph.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filteredDocs.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-4 hover:bg-neutral-light/20 transition-colors group">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-secondary/10 text-secondary">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-foreground line-clamp-1" title={doc.filename}>
                      {doc.filename}
                    </h4>
                    <div className="mt-1 flex items-center gap-3 text-xs text-neutral-dark">
                      <span>{formatBytes(doc.file_size)}</span>
                      <span>•</span>
                      <span>{format(new Date(doc.created_at), 'MMM d, yyyy')}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        {doc.status === 'COMPLETED' && <span className="text-accent flex items-center gap-1"><div className="h-1.5 w-1.5 rounded-full bg-accent"></div> Synced</span>}
                        {doc.status === 'PROCESSING' && <span className="text-secondary flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> Indexing</span>}
                        {doc.status === 'FAILED' && <span className="text-red-500">Failed</span>}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="pl-4">
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    disabled={deleteMutation.isPending}
                    className="flex h-8 w-8 items-center justify-center rounded text-neutral-dark hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                    title="Remove source"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


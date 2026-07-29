import { useState, useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Plus, Search, MessageSquare, Edit2, Trash2, ChevronLeft, FileText, Upload as UploadIcon, Loader2 } from 'lucide-react'
import { useConversations, useCreateConversation, useUpdateConversation, useDeleteConversation, type Conversation } from '@/hooks/useConversations'
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments'
import { DocumentService } from '@/services/DocumentService'
import { isToday, subDays, isAfter } from 'date-fns'
import { cn } from '@/lib/utils'

interface NavigationPanelProps {
  projectId: string
  conversationId?: string
}

type NavTab = 'chats' | 'docs'

export function NavigationPanel({ projectId, conversationId }: NavigationPanelProps) {
  const navigate = useNavigate()
  
  const { data: conversations, isLoading: loadingConversations } = useConversations(projectId)
  const { data: documents, isLoading: loadingDocs, refetch: refetchDocs } = useDocuments()
  
  const createConvMutation = useCreateConversation()
  const updateConvMutation = useUpdateConversation()
  const deleteConvMutation = useDeleteConversation()
  const deleteDocMutation = useDeleteDocument()

  const [activeTab, setActiveTab] = useState<NavTab>('chats')
  const [searchQuery, setSearchQuery] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  const handleNewChat = async () => {
    const conv = await createConvMutation.mutateAsync({ workspace_id: projectId })
    navigate(`/projects/${projectId}/chat/${conv.id}`)
  }

  const handleRename = (e: React.MouseEvent, id: string, currentTitle: string) => {
    e.preventDefault()
    e.stopPropagation()
    const newTitle = prompt('Enter new conversation name:', currentTitle)
    if (newTitle && newTitle.trim() !== currentTitle) {
      updateConvMutation.mutate({ id, title: newTitle.trim() })
    }
  }

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this conversation?')) {
      deleteConvMutation.mutate(id)
      if (conversationId === id) {
        navigate(`/projects/${projectId}/chat`)
      }
    }
  }

  const handleDeleteDoc = async (e: React.MouseEvent, id: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this document?')) {
      await deleteDocMutation.mutateAsync(id)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      setUploadProgress(0)
      await DocumentService.uploadDocument(projectId, file, (progress) => {
        setUploadProgress(progress)
      })
      // Simulating ingestion pipeline after upload
      setTimeout(() => {
        setUploadProgress(null)
        refetchDocs()
      }, 1500)
    } catch (err) {
      console.error(err)
      setUploadProgress(null)
    }
  }

  const groupedConversations = useMemo(() => {
    if (!conversations) return {}
    const filtered = conversations.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()))
    const groups: Record<string, Conversation[]> = { 'Today': [], 'Previous 7 Days': [], 'Older': [] }
    const sevenDaysAgo = subDays(new Date(), 7)
    
    filtered.forEach(conv => {
      const date = new Date(conv.created_at)
      if (isToday(date)) groups['Today'].push(conv)
      else if (isAfter(date, sevenDaysAgo)) groups['Previous 7 Days'].push(conv)
      else groups['Older'].push(conv)
    })
    return groups
  }, [conversations, searchQuery])

  return (
    <div className="flex flex-col h-full bg-[#F8FAFC] shadow-inner">
      <div className="p-4 shrink-0">
        <Link to="/projects" className="flex items-center text-xs font-semibold text-neutral-dark hover:text-foreground mb-4">
          <ChevronLeft className="h-4 w-4 mr-1" /> Back to Hub
        </Link>
        <button 
          onClick={handleNewChat}
          className="w-full flex items-center justify-between rounded-lg bg-white border border-border shadow-sm px-4 py-2.5 text-sm font-bold text-foreground transition-all hover:bg-neutral-50 hover:shadow-md"
        >
          New Chat <Plus className="h-4 w-4 text-neutral-dark" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex px-4 border-b border-border shrink-0">
        <button 
          onClick={() => setActiveTab('chats')}
          className={cn("pb-2 text-xs font-bold uppercase tracking-wider transition-colors relative flex-1 text-left", activeTab === 'chats' ? "text-accent" : "text-neutral-dark hover:text-foreground")}
        >
          Chats
          {activeTab === 'chats' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-full" />}
        </button>
        <button 
          onClick={() => setActiveTab('docs')}
          className={cn("pb-2 text-xs font-bold uppercase tracking-wider transition-colors relative flex-1 text-left", activeTab === 'docs' ? "text-accent" : "text-neutral-dark hover:text-foreground")}
        >
          Documents
          {activeTab === 'docs' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-full" />}
        </button>
      </div>
        
      <div className="px-4 py-3 shrink-0">
         <div className="relative">
           <Search className="absolute left-2.5 top-2 h-4 w-4 text-neutral-dark opacity-70" />
           <input
             type="text"
             placeholder={activeTab === 'chats' ? "Search chats..." : "Search docs..."}
             value={searchQuery}
             onChange={e => setSearchQuery(e.target.value)}
             className="w-full bg-white border border-border rounded-md pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-accent transition-shadow shadow-sm"
           />
         </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4 no-scrollbar">
        {activeTab === 'chats' && (
          loadingConversations ? (
            <div className="px-4 py-4 text-xs text-neutral-dark">Loading...</div>
          ) : (
            Object.entries(groupedConversations).map(([group, convs]) => (
              convs.length > 0 && (
                <div key={group} className="mb-4">
                  <div className="mb-2 px-3 text-[10px] font-bold uppercase tracking-wider text-neutral-dark/70">
                    {group}
                  </div>
                  <div className="space-y-1">
                    {convs.map(conv => (
                      <Link
                        key={conv.id}
                        to={`/projects/${projectId}/chat/${conv.id}`}
                        className={cn(
                          "group relative flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-all duration-200 min-w-0",
                          conversationId === conv.id 
                            ? "bg-white shadow-sm text-foreground font-semibold border border-black/5" 
                            : "text-neutral-dark hover:bg-white/60 hover:text-foreground"
                        )}
                      >
                        <MessageSquare className={cn("h-4 w-4 shrink-0 opacity-70", conversationId === conv.id && "text-accent opacity-100")} />
                        <span className="truncate pr-8 min-w-0">{conv.title}</span>
                        <div className={cn("absolute right-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 bg-white/80 backdrop-blur-sm px-1 rounded", conversationId === conv.id && "bg-white")}>
                          <button onClick={(e) => handleRename(e, conv.id, conv.title)} className="p-1 hover:text-accent rounded-sm"><Edit2 className="h-3.5 w-3.5" /></button>
                          <button onClick={(e) => handleDelete(e, conv.id)} className="p-1 hover:text-red-500 rounded-sm"><Trash2 className="h-3.5 w-3.5" /></button>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )
            ))
          )
        )}

        {activeTab === 'docs' && (
          <div className="px-2">
            <label className="flex items-center justify-center gap-2 w-full border-2 border-dashed border-border rounded-lg p-4 mb-4 cursor-pointer hover:bg-white hover:border-accent transition-colors bg-white/50">
              <UploadIcon className="w-4 h-4 text-neutral-dark" />
              <span className="text-xs font-bold text-neutral-dark">Upload Document</span>
              <input type="file" className="hidden" accept=".pdf,.txt" onChange={handleFileUpload} />
            </label>

            {uploadProgress !== null && (
              <div className="mb-4 bg-white border border-border rounded-lg p-3 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-foreground">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />
                  Ingesting Document...
                </div>
                <div className="w-full bg-neutral-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-accent h-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                </div>
              </div>
            )}

            {loadingDocs ? (
              <div className="px-2 py-4 text-xs text-neutral-dark">Loading docs...</div>
            ) : (
              <div className="space-y-1">
                {documents?.filter(d => d.filename.toLowerCase().includes(searchQuery.toLowerCase())).map(doc => (
                  <div key={doc.id} className="group relative flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-all duration-200 text-neutral-dark hover:bg-white hover:shadow-sm min-w-0">
                    <FileText className="h-4 w-4 shrink-0 opacity-70" />
                    <div className="flex flex-col overflow-hidden min-w-0">
                      <span className="truncate text-foreground font-medium text-xs min-w-0">{doc.filename}</span>
                      <span className="text-[10px] text-neutral-400">{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="absolute right-2 flex items-center opacity-0 transition-opacity group-hover:opacity-100 bg-white/80 backdrop-blur-sm px-1 rounded">
                       <button onClick={(e) => handleDeleteDoc(e, doc.id)} className="p-1 hover:text-red-500 rounded-sm"><Trash2 className="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

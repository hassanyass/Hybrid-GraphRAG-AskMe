import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { Group as PanelGroup, Panel, Separator as PanelResizeHandle, type PanelImperativeHandle } from 'react-resizable-panels'
import { useWorkspace } from '@/hooks/useWorkspaces'
import { useDocuments } from '@/hooks/useDocuments'
import { useConversation } from '@/hooks/useConversations'
import { useChatQuery, type ChatProgressState } from '@/hooks/useChat'
import { useWorkspaceMode } from '@/contexts/WorkspaceModeContext'
import { useWorkspaceLayoutStore } from '@/store/uiStore'
import { ConversationService } from '@/services/ConversationService'
import { useQueryClient } from '@tanstack/react-query'

import { NavigationPanel } from './components/NavigationPanel'
import { WorkspaceHeader } from './components/WorkspaceHeader'
import { ChatInput } from './components/ChatInput'
import { ThinkingStatus } from './components/ThinkingStatus'
import { ChatMessage, type MessageProps } from './ChatMessage'
import { SourcesPane } from './SourcesPane'
import { GraphPane } from './GraphPane'
import { AdvancedDocumentPane } from './components/AdvancedDocumentPane'
import { cn } from '@/lib/utils'

type Tab = 'sources' | 'graph' | 'document'

export function ChatWorkspace() {
  const { projectId, conversationId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  
  const { mode } = useWorkspaceMode()
  const { data: workspace } = useWorkspace(projectId)
  const { data: activeConversation } = useConversation(conversationId)
  
  const chatMutation = useChatQuery()

  const {
    leftPanelOpen,
    rightPanelOpen,
    panelSizes,
    setPanelSizes,
    setLeftPanelOpen,
    setRightPanelOpen,
    toggleLeftPanel,
    toggleRightPanel
  } = useWorkspaceLayoutStore()

  const [messages, setMessages] = useState<MessageProps[]>([])
  const [activeSources, setActiveSources] = useState<Source[]>([])
  const [activeEntities, setActiveEntities] = useState<Entity[]>([])
  const [activeRelationships, setActiveRelationships] = useState<Relationship[]>([])
  const [activeTab, setActiveTab] = useState<Tab>('sources')
  
  // Read documentId passed from URL query
  const urlDocumentId = searchParams.get('document')
  console.log('[DEBUG] ChatWorkspace INITIALIZED. Query documentId:', urlDocumentId)

  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(urlDocumentId || null)
  
  // Issue 2: Workspace Document Ownership (Fetch and auto-select latest if empty)
  const { data: documents } = useDocuments()
  
  useEffect(() => {
    // If we already have a document selected via URL, do nothing
    if (searchParams.get('document')) return
    // Wait until we have documents and a projectId
    if (!documents || !projectId) return

    // Find documents for this workspace that are completed
    const workspaceDocs = documents.filter(
      doc => doc.workspace_id === projectId && doc.status === 'COMPLETED'
    )
    
    if (workspaceDocs.length > 0) {
      // Sort to find the most recently updated/created document
      const latestDoc = workspaceDocs.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )[0]
      
      console.log('[DEBUG] Auto-selecting latest workspace document:', latestDoc.id)
      setActiveDocumentId(latestDoc.id)
      
      const newParams = new URLSearchParams(searchParams)
      newParams.set('document', latestDoc.id)
      setSearchParams(newParams, { replace: true })
    }
  }, [documents, projectId, searchParams, setSearchParams])

  // Sync to URL when local state changes
  useEffect(() => {
    if (activeDocumentId && activeDocumentId !== searchParams.get('document')) {
      const newParams = new URLSearchParams(searchParams)
      newParams.set('document', activeDocumentId)
      setSearchParams(newParams, { replace: true })
    }
  }, [activeDocumentId, searchParams, setSearchParams])

  // Also listen for URL param changes (e.g. refresh, direct link, upload navigate)
  useEffect(() => {
    const currentDoc = searchParams.get('document')
    if (currentDoc) {
      if (currentDoc !== activeDocumentId) {
         setActiveDocumentId(currentDoc)
      }
      if (!rightPanelOpen) {
         console.log('[DEBUG] Auto-opening Document Pane for query document:', currentDoc)
         setActiveTab('document')
         setRightPanelOpen(true)
      }
    }
  }, [searchParams, rightPanelOpen])

  const [highlightText, setHighlightText] = useState<string | undefined>()
  const [initialPage, setInitialPage] = useState<number | undefined>()
  
  const [chatState, setChatState] = useState<ChatProgressState>('done')

  // Local conversation ID state — starts from URL param, updated after creation
  const [activeConvId, setActiveConvId] = useState<string | undefined>(conversationId)
  
  // Sync activeConvId when URL param changes (e.g. user clicks a conversation in sidebar)
  useEffect(() => {
    if (conversationId) {
      setActiveConvId(conversationId)
    }
  }, [conversationId])
  
  const bottomRef = useRef<HTMLDivElement>(null)
  const leftPanelRef = useRef<PanelImperativeHandle>(null)
  const rightPanelRef = useRef<PanelImperativeHandle>(null)

  useEffect(() => {
    if (mode === 'chat' || !projectId) {
      setLeftPanelOpen(false)
      setRightPanelOpen(false)
    }
  }, [mode, projectId, setLeftPanelOpen, setRightPanelOpen])

  useEffect(() => {
    if (leftPanelOpen) {
      leftPanelRef.current?.expand()
    } else {
      leftPanelRef.current?.collapse()
    }
  }, [leftPanelOpen])

  useEffect(() => {
    if (rightPanelOpen) {
      if (rightPanelRef.current?.getSize() === 0) {
        rightPanelRef.current?.resize(35)
      } else {
        rightPanelRef.current?.expand()
      }
    } else {
      rightPanelRef.current?.collapse()
    }
  }, [rightPanelOpen])

  useEffect(() => {
    if (activeConversation) {
      const mapped = activeConversation.messages.map(m => ({
        role: m.role,
        content: m.content,
        message_id: m.id
      }))
      setMessages(mapped.length ? mapped : [{
        role: 'assistant',
        content: `Hello! I am your research assistant for **${workspace?.name || 'this space'}**. How can I help you today?`
      }])
    } else {
      setMessages([{
        role: 'assistant',
        content: `Hello! I am your research assistant for **${workspace?.name || 'this space'}**. How can I help you today?`
      }])
    }
  }, [activeConversation, workspace])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatState])

  /**
   * Ensure a real conversation UUID exists before sending any message.
   * If no conversation exists, create one via the backend API,
   * update local state, and update the URL without reloading.
   */
  async function ensureConversation(): Promise<string> {
    // If we already have a valid conversation ID, reuse it
    if (activeConvId) {
      return activeConvId
    }

    // No conversation yet — create one via the existing backend endpoint
    if (!projectId) {
      throw new Error('Cannot create conversation: workspace ID is missing.')
    }

    const newConv = await ConversationService.createConversation({
      workspace_id: projectId,
      title: 'New Chat',
    })

    const newId = newConv.id

    // Update local state so subsequent messages reuse this conversation
    setActiveConvId(newId)

    // Update URL to include the real conversation UUID (no page reload)
    navigate(`/projects/${projectId}/chat/${newId}`, { replace: true })

    // Invalidate conversation list so sidebar reflects the new conversation
    queryClient.invalidateQueries({ queryKey: ['conversations', projectId] })

    return newId
  }

  const handleSubmit = async (text: string, retrievalMode: string, language: string) => {
    if (!projectId) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    
    try {
      // Obtain a real conversation UUID — create if needed
      const convId = await ensureConversation()

      const response = await chatMutation.mutateAsync({
        workspace_id: projectId,
        conversation_id: convId,
        query: text,
        retrievalMode: retrievalMode as any,
        responseLanguage: language,
        onProgress: (state) => {
          setChatState(state)
        }
      })
      
      setActiveSources(response.retrieved_chunks || [])
      setActiveEntities(response.graph_entities || [])
      setActiveRelationships(response.graph_relationships || [])
      
      if (!rightPanelOpen && (response.retrieved_chunks?.length || response.graph_entities?.length)) {
         setRightPanelOpen(true)
         setActiveTab('sources')
      }

      const answer = response.answer || "Unable to generate a clear answer from the sources."
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '',
        message_id: response.message_id
      }])

      let i = 0
      const typingInterval = setInterval(() => {
        setMessages(prev => {
          const newMsg = [...prev]
          newMsg[newMsg.length - 1] = {
            ...newMsg[newMsg.length - 1],
            content: answer.slice(0, i),
            isTyping: i < answer.length
          }
          return newMsg
        })
        i += 4
        if (i >= answer.length) {
          clearInterval(typingInterval)
        }
      }, 10)

    } catch (error) {
      setChatState('done')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'An error occurred while communicating with the enterprise knowledge base. Please try again.'
      }])
    }
  }

  const handleVoiceSubmit = async (blob: Blob, retrievalMode: string, language: string) => {
    if (!projectId) return
    
    setMessages(prev => [...prev, { role: 'user', content: '🎤 *Sent a voice message*' }])
    
    try {
      // Obtain a real conversation UUID — create if needed
      const convId = await ensureConversation()

      const response = await chatMutation.mutateAsync({
        workspace_id: projectId,
        conversation_id: convId,
        audioBlob: blob,
        retrievalMode: retrievalMode as any,
        responseLanguage: language,
        onProgress: (state) => {
          setChatState(state)
        }
      })
      
      setActiveSources(response.retrieved_chunks || [])
      setActiveEntities(response.graph_entities || [])
      setActiveRelationships(response.graph_relationships || [])
      
      const answer = response.answer || ""
      
      setMessages(prev => {
        const newMsg = [...prev]
        newMsg[newMsg.length - 1] = {
          role: 'user',
          content: `🎤 *Transcription:* ${response.transcription}`
        }
        newMsg.push({
          role: 'assistant',
          content: '',
          audioBase64: response.audio_base64,
          detectedLanguage: response.detected_language,
          message_id: response.message_id
        })
        return newMsg
      })

      let i = 0
      const typingInterval = setInterval(() => {
        setMessages(prev => {
          const newMsg = [...prev]
          newMsg[newMsg.length - 1] = {
            ...newMsg[newMsg.length - 1],
            content: answer.slice(0, i),
            isTyping: i < answer.length
          }
          return newMsg
        })
        i += 4
        if (i >= answer.length) {
          clearInterval(typingInterval)
        }
      }, 10)
    } catch (error) {
      setChatState('done')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'An error occurred while generating a response. Please try again.'
      }])
    }
  }
  
  const handleSourceClick = (source: any) => {
    console.log('[DEBUG] handleSourceClick EXECUTED')
    console.log('[DEBUG] clicked source:', source)
    console.log('[DEBUG] document_id:', source.document_id)
    console.log('[DEBUG] page_number:', source.page_number)
    console.log('[DEBUG] filename:', source.filename)
    console.log('[DEBUG] activeDocumentId BEFORE:', activeDocumentId)

    if (source.document_id) {
       setActiveDocumentId(source.document_id)
       if (source.page_number) setInitialPage(source.page_number)
       if (source.text) setHighlightText(source.text.substring(0, 30))
       else if (source.content) setHighlightText(source.content.substring(0, 30))
    }
    setActiveTab('document')
    setRightPanelOpen(true)
    
    // We can't log 'AFTER' synchronously since state updates are async,
    // but we can log the exact values we're trying to set.
    console.log('[DEBUG] Attempting to set activeDocumentId to:', source.document_id)
  }
  
  const handleCitationClick = (citationText: string) => {
    let docId = citationText.split(' ')[0]
    const matchedSource = activeSources.find(s => 
      s.document_id === docId || s.text?.includes(docId)
    )
    if (matchedSource?.document_id) {
       setActiveDocumentId(matchedSource.document_id)
       if (matchedSource.page_number) setInitialPage(matchedSource.page_number)
       if (matchedSource.content) setHighlightText(matchedSource.content.substring(0, 30))
    } else if (activeSources.length > 0 && activeSources[0].document_id) {
       setActiveDocumentId(activeSources[0].document_id)
       if (activeSources[0].page_number) setInitialPage(activeSources[0].page_number)
       if (activeSources[0].content) setHighlightText(activeSources[0].content.substring(0, 30))
    }
    setActiveTab('document')
    setRightPanelOpen(true)
  }

  return (
    <PanelGroup 
      id="chat-workspace-layout"
      orientation="horizontal" 
      defaultLayout={{
        'nav-panel': panelSizes.nav,
        'chat-panel': panelSizes.chat,
        'context-panel': panelSizes.context
      }}
      onLayoutChanged={(layout) => {
        setPanelSizes({
          nav: layout['nav-panel'],
          chat: layout['chat-panel'],
          context: layout['context-panel']
        })
        
        if (layout['context-panel'] === 0 && rightPanelOpen) {
          setRightPanelOpen(false)
        } else if (layout['context-panel'] > 0 && !rightPanelOpen) {
          setRightPanelOpen(true)
        }

        if (layout['nav-panel'] === 0 && leftPanelOpen) {
          setLeftPanelOpen(false)
        } else if (layout['nav-panel'] > 0 && !leftPanelOpen) {
          setLeftPanelOpen(true)
        }
      }}
      className="h-full w-full bg-[#F8FAFC] overflow-hidden font-sans"
    >
       <Panel 
         panelRef={leftPanelRef}
         id="nav-panel" 
         collapsible 
         collapsedSize={0}
         defaultSize={`${panelSizes.nav}`} 
         minSize="15" 
         maxSize="28"
       >
         {projectId && <NavigationPanel projectId={projectId} conversationId={activeConvId} />}
       </Panel>
       
       <PanelResizeHandle className="w-[1px] bg-border hover:bg-accent hover:w-1 transition-all cursor-col-resize z-50" />

      <Panel id="chat-panel" defaultSize={`${panelSizes.chat}`} minSize="35" className="flex flex-col bg-white border-x border-border relative min-w-0">
        
        <WorkspaceHeader 
          workspaceName={workspace?.name}
          isLeftPaneOpen={leftPanelOpen}
          toggleLeftPane={mode !== 'chat' ? toggleLeftPanel : undefined}
          isRightPaneOpen={rightPanelOpen}
          toggleRightPane={toggleRightPanel}
        />

        <div className="flex-1 overflow-y-auto overflow-x-hidden pt-6 px-4 md:px-8 xl:px-12 no-scrollbar scroll-smooth min-w-0">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} {...msg} sources={activeSources} onCitationClick={handleCitationClick} />
          ))}
          
          {chatState !== 'done' && (
            <div className="flex w-full mb-6 max-w-4xl mx-auto min-w-0">
              <ThinkingStatus state={chatState} />
            </div>
          )}
          
          <div ref={bottomRef} className="h-10" />
        </div>

        <div className="w-full min-w-0 shrink-0">
          <ChatInput 
            isPending={chatMutation.isPending}
            onSubmit={handleSubmit}
            onVoiceSubmit={handleVoiceSubmit}
          />
        </div>
      </Panel>

      <PanelResizeHandle className="w-[1px] bg-border hover:bg-accent hover:w-1 transition-all cursor-col-resize z-50" />
      
      <Panel 
        panelRef={rightPanelRef}
        id="context-panel" 
        collapsible
        collapsedSize={0}
        defaultSize={`${panelSizes.context}`} 
        minSize="22" 
        maxSize="45" 
        className="flex flex-col bg-[#F8FAFC] overflow-hidden"
      >
        <div className="flex px-4 pt-4 border-b border-border bg-neutral-50/50">
          <div className="flex w-full gap-4 overflow-x-auto no-scrollbar">
            <button onClick={() => setActiveTab('sources')} className={cn("pb-3 text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap", activeTab === 'sources' ? "text-accent" : "text-neutral-dark hover:text-foreground")}>
              Sources {activeTab === 'sources' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-full" />}
            </button>
            <button onClick={() => setActiveTab('document')} className={cn("pb-3 text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap", activeTab === 'document' ? "text-accent" : "text-neutral-dark hover:text-foreground")}>
              Document {activeTab === 'document' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-full" />}
            </button>
            <button onClick={() => setActiveTab('graph')} className={cn("pb-3 text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap", activeTab === 'graph' ? "text-accent" : "text-neutral-dark hover:text-foreground")}>
              Knowledge Graph {activeTab === 'graph' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-full" />}
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-hidden bg-white">
          {activeTab === 'sources' && <SourcesPane sources={activeSources} onSourceClick={handleSourceClick} />}
          {activeTab === 'document' && <AdvancedDocumentPane documentId={activeDocumentId} highlightText={highlightText} initialPage={initialPage} />}
          {activeTab === 'graph' && <GraphPane entities={activeEntities} relationships={activeRelationships} />}
        </div>
      </Panel>
    </PanelGroup>
  )
}

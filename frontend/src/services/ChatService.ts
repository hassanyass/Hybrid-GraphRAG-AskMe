import { apiClient } from '@/api/client'

export interface Source {
  chunk_id?: string
  document_id?: string
  filename?: string
  page_number?: number
  section_title?: string
  score?: number
  text?: string
  preview?: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Entity {
  id: string
  label: string
  properties: Record<string, any>
}

export interface QueryResponse {
  answer: string
  retrieved_chunks?: Source[]
  graph_entities?: Entity[]
  confidence?: number
  audio_base64?: string
  detected_language?: string
  transcription?: string
}

export interface ChatRequestPayload {
  workspace_id: string
  conversation_id: string
  query?: string
  audioBlob?: Blob
  retrievalMode?: 'hybrid' | 'vector' | 'graph'
}

export type ChatProgressState = 
  | 'understanding' 
  | 'searching' 
  | 'retrieving' 
  | 'ranking' 
  | 'generating' 
  | 'done'

export class ChatService {
  /**
   * Submit a query and simulate a streamed progress sequence.
   * In the future, this can be swapped with real SSE without breaking the UI.
   */
  static async submitQuery(
    payload: ChatRequestPayload,
    onProgress: (state: ChatProgressState) => void
  ): Promise<QueryResponse> {
    
    // Simulate initial RAG pipeline steps for UX
    onProgress('understanding')
    await new Promise(resolve => setTimeout(resolve, 600))
    
    onProgress('searching')
    await new Promise(resolve => setTimeout(resolve, 800))
    
    onProgress('retrieving')
    
    // Execute real backend call while simulating 'generating'
    const requestPromise = payload.audioBlob 
      ? this.submitVoiceQuery(payload)
      : this.submitTextQuery(payload)

    // Wait slightly to show retrieving, then switch to generating while waiting for response
    await new Promise(resolve => setTimeout(resolve, 800))
    onProgress('ranking')
    await new Promise(resolve => setTimeout(resolve, 600))
    
    onProgress('generating')
    const response = await requestPromise
    onProgress('done')
    
    return response
  }

  private static async submitTextQuery(payload: ChatRequestPayload): Promise<QueryResponse> {
    const res = await apiClient.post<QueryResponse>('/chat/query', {
      question: payload.query,
      workspace_id: payload.workspace_id,
      conversation_id: payload.conversation_id
    })
    return res.data
  }

  private static async submitVoiceQuery(payload: ChatRequestPayload): Promise<QueryResponse> {
    const formData = new FormData()
    formData.append('audio', payload.audioBlob!, 'recording.webm')
    formData.append('workspace_id', payload.workspace_id)
    formData.append('conversation_id', payload.conversation_id)
    
    const res = await apiClient.post<QueryResponse>('/chat/voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return res.data
  }
}

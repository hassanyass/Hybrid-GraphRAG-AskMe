import { apiClient } from '@/api/client'
import { Message } from './ChatService'

export interface Conversation {
  id: string
  user_id: string
  workspace_id: string
  title: string
  created_at: string
  updated_at: string
  messages: Message[]
}

export interface ConversationCreate {
  workspace_id: string
  title?: string
}

export class ConversationService {
  static async listConversations(workspaceId: string): Promise<Conversation[]> {
    const response = await apiClient.get<Conversation[]>(`/conversations/workspace/${workspaceId}`)
    return response.data
  }

  static async getConversation(id: string): Promise<Conversation> {
    const response = await apiClient.get<Conversation>(`/conversations/${id}`)
    return response.data
  }

  static async createConversation(data: ConversationCreate): Promise<Conversation> {
    const response = await apiClient.post<Conversation>('/conversations/', data)
    return response.data
  }

  static async updateConversation(id: string, title: string): Promise<Conversation> {
    const response = await apiClient.patch<Conversation>(`/conversations/${id}`, { title })
    return response.data
  }

  static async deleteConversation(id: string): Promise<void> {
    await apiClient.delete(`/conversations/${id}`)
  }
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ConversationService, type Conversation, type ConversationCreate } from '@/services/ConversationService'

export type { Conversation, ConversationCreate } from '@/services/ConversationService'

export function useConversations(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ['conversations', workspaceId],
    queryFn: async () => {
      if (!workspaceId) throw new Error('Workspace ID is required')
      return ConversationService.listConversations(workspaceId)
    },
    enabled: !!workspaceId
  })
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: async () => {
      if (!id) throw new Error('Conversation ID is required')
      return ConversationService.getConversation(id)
    },
    enabled: !!id
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: ConversationCreate) => {
      return ConversationService.createConversation(data)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations', data.workspace_id] })
    }
  })
}

export function useUpdateConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, title }: { id: string, title: string }) => {
      return ConversationService.updateConversation(id, title)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['conversation', data.id] })
    }
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await ConversationService.deleteConversation(id)
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    }
  })
}

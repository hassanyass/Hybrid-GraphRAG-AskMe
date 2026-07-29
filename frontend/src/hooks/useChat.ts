import { useMutation } from '@tanstack/react-query'
import { ChatService, ChatRequestPayload, ChatProgressState, QueryResponse } from '@/services/ChatService'
export type { Source, Entity, ChatProgressState, QueryResponse } from '@/services/ChatService'

interface ChatMutationVariables extends ChatRequestPayload {
  onProgress: (state: ChatProgressState) => void
}

export function useChatQuery() {
  return useMutation({
    mutationFn: async (variables: ChatMutationVariables) => {
      const { onProgress, ...payload } = variables
      return ChatService.submitQuery(payload, onProgress)
    },
  })
}

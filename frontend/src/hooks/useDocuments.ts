import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DocumentService, type DocumentResponse, type DocumentUploadResponse } from '@/services/DocumentService'

export type { DocumentResponse, DocumentUploadResponse }

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      return DocumentService.listDocuments()
    }
  })
}

export function useDocumentDetails(id: string | null) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      return DocumentService.getDocument(id!)
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'COMPLETED' || status === 'FAILED') return false
      return 2000
    }
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ workspace_id, file, onProgress }: { workspace_id: string, file: File, onProgress?: (p: any) => void }) => {
      return DocumentService.uploadDocument(workspace_id, file, onProgress)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    }
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await DocumentService.deleteDocument(id)
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    }
  })
}

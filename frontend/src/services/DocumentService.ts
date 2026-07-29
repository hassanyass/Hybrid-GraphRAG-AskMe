import { apiClient } from '@/api/client'

export interface DocumentResponse {
  id: string
  workspace_id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  chunk_count?: number
  page_count?: number
  created_at: string
  updated_at: string
}

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  status: string
  created_at: string
}

export class DocumentService {
  /**
   * Upload a document to a workspace.
   */
  static async uploadDocument(
    workspaceId: string, 
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)

    const response = await apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })
    
    return response.data
  }

  /**
   * Retrieve all documents for the current user.
   */
  static async listDocuments(): Promise<DocumentResponse[]> {
    const response = await apiClient.get<DocumentResponse[]>('/documents')
    return response.data
  }

  /**
   * Get a presigned URL to download/view the document.
   */
  static async getDocumentUrl(documentId: string): Promise<string> {
    const response = await apiClient.get<{ url: string }>(`/documents/${documentId}/download`)
    return response.data.url
  }

  /**
   * Delete a document
   */
  static async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`)
  }

  /**
   * Get a single document by ID (used for polling status).
   */
  static async getDocument(documentId: string): Promise<DocumentResponse> {
    const response = await apiClient.get<DocumentResponse>(`/documents/${documentId}`)
    return response.data
  }
}

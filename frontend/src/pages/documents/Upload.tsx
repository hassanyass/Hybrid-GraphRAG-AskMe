import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, CheckCircle2, Loader2, ArrowLeft, Network, AlertTriangle } from 'lucide-react'
import { useUploadDocument, useDocumentDetails } from '@/hooks/useDocuments'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'

type UploadStage = 'IDLE' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export function Upload() {
  const navigate = useNavigate()
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const [stage, setStage] = useState<UploadStage>('IDLE')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const uploadMutation = useUploadDocument()
  
  // Real backend polling — no mocks, no stubs
  const { data: documentDetails, error: pollError } = useDocumentDetails(documentId)

  // Derive backend status directly from the real API response
  const backendStatus = documentDetails?.status

  // Sync frontend stage from backend status
  useEffect(() => {
    if (!backendStatus) return

    if (backendStatus === 'COMPLETED' && stage !== 'COMPLETED') {
      setStage('COMPLETED')
    }
    if (backendStatus === 'FAILED' && stage !== 'FAILED') {
      setStage('FAILED')
    }
  }, [backendStatus, stage])

  // Auto-navigate to chat on COMPLETED
  useEffect(() => {
    if (stage === 'COMPLETED' && projectId) {
      // Invalidate document queries so sidebar/lists reflect the new document
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      
      // Navigate to chat after a brief moment so the user sees the completion state
      const timer = setTimeout(() => {
        navigate(`/projects/${projectId}/chat`)
      }, 1200)
      return () => clearTimeout(timer)
    }
  }, [stage, projectId, navigate, queryClient])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0 || !projectId) return
    
    const file = acceptedFiles[0]
    setStage('UPLOADING')
    setUploadProgress(0)
    setErrorMsg(null)

    try {
      const result = await uploadMutation.mutateAsync({
        file,
        workspace_id: projectId,
        onProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(percentCompleted)
          }
        }
      })
      setDocumentId(result.document_id)
      setStage('PROCESSING')
    } catch (error: any) {
      setStage('FAILED')
      setErrorMsg(error?.response?.data?.detail || 'Failed to upload document')
    }
  }, [uploadMutation, projectId])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
    disabled: stage !== 'IDLE'
  })

  /**
   * Step status logic — based ONLY on real backend statuses.
   * 
   * Backend provides exactly 4 statuses: UPLOADED, PROCESSING, COMPLETED, FAILED.
   * 
   * Mapping:
   *   Step 1 (Upload & Parse):     active during UPLOADING, completed once PROCESSING+
   *   Step 2 (Chunk & Embed):      active during PROCESSING, completed once COMPLETED
   *   Step 3 (Complete):           completed only when COMPLETED
   */
  const getStepStatus = (stepIndex: number): 'waiting' | 'active' | 'completed' | 'error' => {
    if (stage === 'IDLE') return 'waiting'
    if (stage === 'FAILED') return 'error'
    if (stage === 'COMPLETED') return 'completed'

    // UPLOADING stage
    if (stage === 'UPLOADING') {
      if (stepIndex === 1) return 'active'
      return 'waiting'
    }

    // PROCESSING stage (backend is chunking + embedding + persisting)
    if (stage === 'PROCESSING') {
      if (stepIndex === 1) return 'completed'
      if (stepIndex === 2) return 'active'
      return 'waiting'
    }

    return 'waiting'
  }

  // Simplified to 3 steps that match the 4 real backend statuses
  const steps = [
    { num: 1, title: 'Uploading & Parsing', desc: 'Securely transferring and extracting raw text' },
    { num: 2, title: 'Chunking & Embedding', desc: 'Structuring data and mapping via BGE-M3 vectors' },
    { num: 3, title: 'Knowledge Ready', desc: 'All processing complete — ready for conversation' },
  ]

  return (
    <div className="mx-auto max-w-3xl animate-in fade-in duration-500 h-full p-6 md:p-8 overflow-y-auto">
      <div className="mb-10 flex items-center gap-4">
        <button 
          onClick={() => navigate('/projects')} 
          className="rounded p-2 text-neutral-dark hover:bg-neutral-light hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Teach Knowledge Space</h1>
          <p className="mt-1 text-neutral-dark">Provide documents to expand your interactive knowledge space.</p>
        </div>
      </div>

      <div className="rounded border border-border bg-white p-8">
        {stage === 'IDLE' && (
          <div 
            {...getRootProps()} 
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed p-16 transition-all duration-200",
              isDragActive ? "border-accent bg-accent/5" : "border-border hover:border-accent/50 hover:bg-neutral-light/30",
              isDragReject && "border-red-500 bg-red-50"
            )}
          >
            <input {...getInputProps()} />
            <div className="rounded-full bg-neutral-light/50 p-4 mb-6">
              <UploadCloud className="h-8 w-8 text-neutral-dark" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">
              {isDragActive ? "Drop document here" : "Click or drag to provide knowledge"}
            </h3>
            <p className="mt-2 text-neutral-dark text-center">
              Supports PDF, DOCX, and TXT (up to 50MB)
            </p>
          </div>
        )}

        {stage !== 'IDLE' && (
          <div className="space-y-10">
            {stage === 'UPLOADING' && (
              <div className="space-y-3">
                <div className="flex justify-between text-sm font-medium text-foreground">
                  <span>Transferring document...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded bg-neutral-light">
                  <div 
                    className="h-full bg-accent transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div>
              <h4 className="font-semibold text-lg text-foreground mb-8">Ingestion Pipeline</h4>
              <div className="space-y-0">
                {steps.map((step, idx) => {
                  const status = getStepStatus(step.num)
                  
                  return (
                    <div key={step.num} className="flex gap-6 relative">
                      <div className="flex flex-col items-center">
                        <div className={cn(
                          "relative z-10 flex h-8 w-8 items-center justify-center rounded-sm border-2 bg-white transition-colors",
                          status === 'completed' && "border-accent text-accent",
                          status === 'active' && "border-accent text-accent",
                          status === 'waiting' && "border-neutral-light text-neutral-dark",
                          status === 'error' && "border-red-500 text-red-500"
                        )}>
                          {status === 'completed' ? <CheckCircle2 className="h-4 w-4" /> : 
                           status === 'active' ? <Loader2 className="h-4 w-4 animate-spin" /> : 
                           status === 'error' ? <AlertTriangle className="h-4 w-4" /> :
                           <span className="text-xs font-bold">{step.num}</span>}
                        </div>
                        {idx !== steps.length - 1 && (
                          <div className={cn(
                            "absolute left-4 top-8 -bottom-4 w-px transition-colors",
                            status === 'completed' ? "bg-accent" : "bg-border"
                          )} />
                        )}
                      </div>
                      <div className="pb-8 pt-1">
                        <p className={cn(
                          "font-medium",
                          status === 'active' && "text-foreground",
                          status === 'completed' && "text-foreground",
                          status === 'waiting' && "text-neutral-dark",
                          status === 'error' && "text-red-600"
                        )}>
                          {step.title}
                        </p>
                        <p className="text-sm text-neutral-dark mt-1">{step.desc}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {stage === 'COMPLETED' && (
              <div className="flex flex-col sm:flex-row items-center gap-4 pt-6 border-t border-border animate-in fade-in">
                <div className="flex items-center gap-2 text-accent font-medium">
                  <CheckCircle2 className="h-5 w-5" />
                  <span>Processing complete — navigating to chat...</span>
                </div>
              </div>
            )}

            {stage === 'FAILED' && (
              <div className="rounded border border-red-200 bg-red-50 p-6 text-red-700">
                <p className="font-semibold text-lg mb-1">Document processing failed.</p>
                <p className="text-sm">{errorMsg || pollError?.message || 'The pipeline encountered an error during processing.'}</p>
                <div className="flex gap-3 mt-4">
                  <button 
                    className="rounded border border-red-200 px-4 py-2 text-sm font-medium hover:bg-red-100 transition-colors"
                    onClick={() => { setStage('IDLE'); setDocumentId(null); setErrorMsg(null); }}
                  >
                    Retry Upload
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

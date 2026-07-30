import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Network, ArrowRight, Loader2, BookOpen, Trash2 } from 'lucide-react'
import { useWorkspaces, useCreateWorkspace, useDeleteWorkspace } from '@/hooks/useWorkspaces'

export function Dashboard() {
  const navigate = useNavigate()
  const { data: workspaces, isLoading, error } = useWorkspaces()
  const createMutation = useCreateWorkspace()
  const deleteMutation = useDeleteWorkspace()
  
  const [isCreating, setIsCreating] = useState(false)
  const [newSpaceName, setNewSpaceName] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSpaceName.trim() || createMutation.isPending) return
    
    try {
      const workspace = await createMutation.mutateAsync({ name: newSpaceName.trim() })
      setNewSpaceName('')
      setIsCreating(false)
      // Navigate to the upload pipeline for the new workspace
      navigate(`/projects/${workspace.id}/upload`)
    } catch (err) {
      console.error("Failed to create workspace:", err)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (window.confirm("Are you sure you want to delete this space? All associated documents and chats will be removed.")) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (err) {
        console.error("Failed to delete workspace:", err)
      }
    }
  }

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-6 text-red-700">
        <h3 className="font-semibold text-lg mb-2">Connection Error</h3>
        <p>Failed to load your knowledge spaces.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl pt-8 animate-in fade-in duration-500">
      <div className="mb-12 flex justify-between items-end border-b border-border pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">
            Intelligence Hub
          </h1>
          <p className="text-neutral-dark">
            Select a knowledge space to begin or create a new isolated project.
          </p>
        </div>
        {!isCreating && (
          <button 
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-semibold text-primary transition-colors hover:bg-accent-hover"
          >
            <Plus className="h-4 w-4" />
            New Space
          </button>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Creation Block */}
        {isCreating && (
          <div className="flex flex-col items-start rounded border border-border bg-white p-6 shadow-sm">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded bg-accent/10">
              <BookOpen className="h-5 w-5 text-accent" />
            </div>
            <h3 className="text-lg font-bold text-foreground mb-2">Name your space</h3>
            <form onSubmit={handleCreate} className="w-full mt-auto">
              <input
                type="text"
                autoFocus
                placeholder="e.g. Q3 Financial Reports"
                className="w-full rounded border border-border bg-background px-3 py-2 text-sm focus:border-accent focus:outline-none mb-3"
                value={newSpaceName}
                onChange={(e) => setNewSpaceName(e.target.value)}
                disabled={createMutation.isPending}
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="flex-1 rounded border border-border px-3 py-2 text-xs font-semibold text-neutral-dark hover:bg-neutral-light"
                  disabled={createMutation.isPending}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 flex items-center justify-center rounded bg-foreground px-3 py-2 text-xs font-semibold text-background hover:bg-foreground/90"
                  disabled={!newSpaceName.trim() || createMutation.isPending}
                >
                  {createMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Create"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Loading Skeletons */}
        {isLoading && !workspaces && Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-48 rounded border border-border bg-neutral-light/20 animate-pulse"></div>
        ))}

        {/* Workspace Cards */}
        {workspaces?.map((workspace) => (
          <div key={workspace.id} className="group relative">
            <button 
              onClick={() => navigate(`/projects/${workspace.id}/chat`)}
              className="flex w-full h-full flex-col items-start rounded border border-border bg-white p-6 text-left transition-all hover:border-accent hover:shadow-sm"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded bg-secondary/10 text-secondary transition-colors group-hover:bg-secondary group-hover:text-white">
                <Network className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-1 line-clamp-1 pr-8">{workspace.name}</h3>
              <p className="text-xs font-medium text-neutral-dark mb-6">
                Created {new Date(workspace.created_at).toLocaleDateString()}
              </p>
              <div className="mt-auto flex w-full items-center justify-between text-sm font-bold text-accent">
                Enter Space
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </button>
            <button
              onClick={(e) => handleDelete(e, workspace.id)}
              disabled={deleteMutation.isPending}
              className="absolute top-4 right-4 p-2 text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50"
              title="Delete Space"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        
        {!isLoading && workspaces?.length === 0 && !isCreating && (
          <div className="col-span-full flex flex-col items-center justify-center py-20 text-center border border-dashed border-border rounded bg-neutral-light/10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm">
              <BookOpen className="h-6 w-6 text-neutral-dark" />
            </div>
            <p className="text-base font-bold text-foreground mb-1">No knowledge spaces yet</p>
            <p className="text-sm text-neutral-dark mb-6 max-w-sm">
              Create your first space to upload documents and begin generating insights.
            </p>
            <button 
              onClick={() => setIsCreating(true)}
              className="rounded bg-accent px-6 py-2.5 text-sm font-bold text-primary transition-colors hover:bg-accent-hover"
            >
              Create Space
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

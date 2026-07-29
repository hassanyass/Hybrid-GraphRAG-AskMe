import React, { createContext, useContext, useState, ReactNode } from 'react'

export type WorkspaceMode = 'chat' | 'research' | 'knowledge'

interface WorkspaceModeContextType {
  mode: WorkspaceMode
  setMode: (mode: WorkspaceMode) => void
}

const WorkspaceModeContext = createContext<WorkspaceModeContextType | undefined>(undefined)

export function WorkspaceModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<WorkspaceMode>('research')

  return (
    <WorkspaceModeContext.Provider value={{ mode, setMode }}>
      {children}
    </WorkspaceModeContext.Provider>
  )
}

export function useWorkspaceMode() {
  const context = useContext(WorkspaceModeContext)
  if (context === undefined) {
    throw new Error('useWorkspaceMode must be used within a WorkspaceModeProvider')
  }
  return context
}

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface WorkspaceLayoutState {
  leftPanelOpen: boolean
  rightPanelOpen: boolean
  panelSizes: { nav: number; chat: number; context: number }
  toggleLeftPanel: () => void
  toggleRightPanel: () => void
  setLeftPanelOpen: (open: boolean) => void
  setRightPanelOpen: (open: boolean) => void
  setPanelSizes: (sizes: { nav: number; chat: number; context: number }) => void
}

export const useWorkspaceLayoutStore = create<WorkspaceLayoutState>()(
  persist(
    (set) => ({
      leftPanelOpen: true,
      rightPanelOpen: false,
      panelSizes: { nav: 18, chat: 82, context: 0 },
      toggleLeftPanel: () => set((state) => ({ leftPanelOpen: !state.leftPanelOpen })),
      toggleRightPanel: () => set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),
      setLeftPanelOpen: (open) => set({ leftPanelOpen: open }),
      setRightPanelOpen: (open) => set({ rightPanelOpen: open }),
      setPanelSizes: (sizes) => set({ panelSizes: sizes }),
    }),
    {
      name: 'workspace-layout-storage',
    }
  )
)

interface UIState {
  isSidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),
    }),
    {
      name: 'ui-storage',
    }
  )
)

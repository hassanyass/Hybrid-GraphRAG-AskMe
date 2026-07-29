import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AuthProvider } from '@/providers/AuthProvider'
import { ProtectedLayout } from '@/layouts/ProtectedLayout'
import { ProjectLayout } from '@/layouts/ProjectLayout'
import { Login } from '@/pages/auth/Login'
import { Register } from '@/pages/auth/Register'
import { Dashboard } from '@/pages/dashboard/Dashboard'
import { Upload } from '@/pages/documents/Upload'
import { ChatWorkspace } from '@/pages/chat/ChatWorkspace'
import { NotFound } from '@/pages/NotFound'
import { WorkspaceModeProvider } from '@/contexts/WorkspaceModeContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Dashboard Hub Routes (with Global Sidebar) */}
            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route path="/projects" element={<Dashboard />} />
              <Route path="/settings" element={<div className="p-8">Settings Placeholder</div>} />
            </Route>

            {/* Isolated Project Workspace Routes (NotebookLM style, no Global Sidebar) */}
            <Route path="/projects/:projectId" element={
              <WorkspaceModeProvider>
                <ProjectLayout />
              </WorkspaceModeProvider>
            }>
              <Route path="upload" element={<Upload />} />
              <Route path="chat" element={<ChatWorkspace />} />
              <Route path="chat/:conversationId" element={<ChatWorkspace />} />
            </Route>

            {/* 404 Catch All */}
            <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

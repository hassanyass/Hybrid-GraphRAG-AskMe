import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader2, ArrowRight, Paperclip, Globe, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  isPending: boolean
  onSubmit: (text: string, retrievalMode: string, language: string) => void
  onVoiceSubmit: (blob: Blob, retrievalMode: string, language: string) => void
}

export function ChatInput({ isPending, onSubmit, onVoiceSubmit }: ChatInputProps) {
  const [input, setInput] = useState('')
  const [retrievalMode, setRetrievalMode] = useState('hybrid')
  const [language, setLanguage] = useState('en')
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { isRecording, startRecording, stopRecording, audioBlob, clearAudio } = useAudioRecorder((text) => {
    setInput(text)
  })

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !isPending) {
        onSubmit(input.trim(), retrievalMode, language)
        setInput('')
      }
    }
  }

  const handleSubmitClick = () => {
    if ((input.trim() || audioBlob) && !isPending) {
      if (audioBlob) {
        onVoiceSubmit(audioBlob, retrievalMode, language)
        clearAudio()
      } else {
        onSubmit(input.trim(), retrievalMode, language)
      }
      setInput('')
    }
  }

  return (
    <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent pt-10">
      <div className="mx-auto flex flex-col w-full max-w-4xl rounded-xl border border-border bg-white shadow-sm focus-within:border-accent focus-within:shadow-[0_0_0_2px_rgba(146,94,120,0.1)] transition-all">
        
        {/* Options Bar */}
        <div className="flex items-center gap-4 px-3 py-2 border-b border-border/50 bg-neutral-50/50 rounded-t-xl overflow-x-auto no-scrollbar shrink-0">
          <div className="flex items-center gap-1.5 text-xs">
            <Database className="w-3.5 h-3.5 text-neutral-400" />
            <select 
              value={retrievalMode}
              onChange={e => setRetrievalMode(e.target.value)}
              className="bg-transparent text-neutral-dark font-medium focus:outline-none cursor-pointer"
            >
              <option value="hybrid">Hybrid Search</option>
              <option value="vector">Vector Only</option>
              <option value="graph">Graph Only</option>
            </select>
          </div>
          <div className="w-px h-3 bg-border" />
          <div className="flex items-center gap-1.5 text-xs">
            <Globe className="w-3.5 h-3.5 text-neutral-400" />
            <select 
              value={language}
              onChange={e => setLanguage(e.target.value)}
              className="bg-transparent text-neutral-dark font-medium focus:outline-none cursor-pointer"
            >
              <option value="en">English</option>
              <option value="ar">Arabic</option>
            </select>
          </div>
        </div>

        <div className="flex items-end gap-2 p-2 relative">
          <button className="absolute left-3 top-3.5 p-1.5 text-neutral-400 hover:text-accent hover:bg-accent/10 rounded-md transition-colors" title="Attach Document">
            <Paperclip className="w-4 h-4" />
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? "Listening to voice input..." : "Ask your enterprise knowledge base..."}
            className="max-h-32 min-h-[44px] w-full resize-none bg-transparent py-3 pl-10 pr-4 text-[15px] focus:outline-none disabled:opacity-50 no-scrollbar text-foreground placeholder:text-neutral-400"
            rows={1}
            disabled={isPending || isRecording}
            dir="auto"
          />
          
          <div className="flex items-center gap-2 pr-2 pb-1.5 shrink-0">
            {isRecording ? (
              <Button 
                size="icon" 
                variant="default" 
                className="bg-red-500 hover:bg-red-600 text-white rounded-lg h-10 w-10 animate-pulse shadow-sm"
                onClick={stopRecording}
              >
                <Square className="h-4 w-4 fill-current" />
              </Button>
            ) : (
              <Button 
                size="icon" 
                variant="outline"
                className={cn(
                  "rounded-lg h-10 w-10 border-border transition-all text-neutral-dark hover:text-foreground hover:bg-neutral-50 shadow-sm",
                  (input.length > 0 || audioBlob) && "hidden md:flex"
                )}
                onClick={() => startRecording(language)}
                disabled={isPending}
                title="Voice query"
              >
                <Mic className="h-4 w-4" />
              </Button>
            )}

            <Button
              size="icon"
              className={cn(
                "rounded-lg h-10 w-10 transition-all shadow-sm",
                (input.length > 0 || audioBlob) ? "bg-accent text-primary-foreground hover:bg-accent-hover hover:shadow-md hover:-translate-y-0.5" : "bg-neutral-100 text-neutral-400 opacity-70"
              )}
              onClick={handleSubmitClick}
              disabled={isPending || isRecording || (input.trim().length === 0 && !audioBlob)}
            >
              {isPending ? <Loader2 className="h-4 w-4 animate-spin text-accent" /> : <ArrowRight className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
      <div className="mx-auto w-full max-w-4xl mt-3 text-center text-[11px] text-neutral-400">
        Enterprise Knowledge Assistant • Shift + Enter for new line
      </div>
    </div>
  )
}

import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { Play, Square, Network, ThumbsUp, ThumbsDown, Copy, Check, Volume2, Loader2 } from 'lucide-react'
import { useRef, useState, useEffect } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { ChatService } from '@/services/ChatService'

export interface MessageProps {
  role: 'user' | 'assistant'
  content: string
  audioBase64?: string
  detectedLanguage?: string
  isTyping?: boolean
  sources?: any[]
  onCitationClick?: (citationText: string) => void
  message_id?: string
}

function LoadingIndicator() {
  const [step, setStep] = useState(0)
  const steps = [
    "Searching knowledge base...",
    "Analyzing documents...",
    "Generating answer..."
  ]

  useEffect(() => {
    const intervals = [
      setTimeout(() => setStep(1), 1500),
      setTimeout(() => setStep(2), 3500)
    ]
    return () => intervals.forEach(clearTimeout)
  }, [])

  return (
    <div className="flex flex-col gap-2 my-2">
      <div className="flex items-center gap-2 h-6 text-sm text-neutral-dark font-medium italic">
        {steps[step]}
        <div className="flex items-center gap-1 ml-1">
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

const CodeBlock = ({ inline, className, children, ...props }: any) => {
  const [copied, setCopied] = useState(false)
  const match = /language-(\w+)/.exec(className || '')
  
  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).replace(/\n$/, ''))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!inline && match) {
    return (
      <div className="relative group my-4 rounded-md overflow-hidden bg-[#1E1E1E]">
        <div className="flex items-center justify-between px-4 py-1.5 bg-[#2D2D2D] text-xs text-neutral-300 font-mono">
          <span>{match[1]}</span>
          <button onClick={handleCopy} className="hover:text-white transition-colors flex items-center gap-1">
            {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={match[1]}
          PreTag="div"
          customStyle={{ margin: 0, padding: '1rem', fontSize: '0.875rem' }}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    )
  }
  
  return (
    <code className={cn("bg-neutral-light/50 text-accent px-1.5 py-0.5 rounded text-sm font-mono", className)} {...props}>
      {children}
    </code>
  )
}

function CitationBadge({ text, onCitationClick, sources }: { text: string, onCitationClick?: (t: string) => void, sources?: any[] }) {
  const [isOpen, setIsOpen] = useState(false)
  
  let docId = text.split(' ')[0]
  const matchedSource = sources?.find(s => 
    s.document_id === docId || s.text?.includes(docId)
  )

  return (
    <span className="relative inline-block" onMouseEnter={() => setIsOpen(true)} onMouseLeave={() => setIsOpen(false)}>
      <button 
        onClick={() => onCitationClick && onCitationClick(text)}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-accent/10 text-accent text-xs font-semibold mx-1 border border-accent/20 cursor-pointer shadow-sm transition-colors hover:bg-accent/20 hover:border-accent/40 align-middle"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        {text}
      </button>

      {isOpen && matchedSource && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 bg-white rounded-lg shadow-xl border border-border p-3 z-50 animate-in fade-in zoom-in-95 duration-200">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">
            Source Evidence
          </div>
          <div className="text-xs text-foreground leading-relaxed line-clamp-4 italic bg-neutral-50 p-2 rounded border border-border/50">
            "{matchedSource.content || matchedSource.text}"
          </div>
          <div className="text-[10px] text-accent mt-2 font-medium flex justify-between items-center">
            <span>Score: {Math.round((matchedSource.score || 0) * 100)}%</span>
            <span>Click to view PDF</span>
          </div>
        </div>
      )}
    </span>
  )
}

export function ChatMessage({ role, content, audioBase64, detectedLanguage, isTyping, sources, onCitationClick, message_id }: MessageProps) {
  const isAI = role === 'assistant'
  const isArabic = detectedLanguage === 'ar' || /[\u0600-\u06FF]/.test(content)
  
  const markdownComponents: Components = {
    code: CodeBlock as any,
    table: ({ node, ...props }: any) => (
      <div className="w-full overflow-x-auto my-6 rounded-lg border border-border">
        <table className="w-full text-sm text-left" {...props} />
      </div>
    ),
    thead: ({ node, ...props }: any) => <thead className="bg-neutral-light/30 text-neutral-dark uppercase text-xs" {...props} />,
    th: ({ node, ...props }: any) => <th className="px-4 py-3 font-semibold border-b border-border" {...props} />,
    td: ({ node, ...props }: any) => <td className="px-4 py-3 border-b border-border/50" {...props} />,
    h1: ({ node, ...props }: any) => <h1 className="text-xl font-bold mt-6 mb-4 text-foreground border-b border-border/30 pb-2" {...props} />,
    h2: ({ node, ...props }: any) => <h2 className="text-lg font-bold mt-5 mb-3 text-foreground" {...props} />,
    h3: ({ node, ...props }: any) => <h3 className="text-base font-bold mt-4 mb-2 text-foreground" {...props} />,
    ul: ({ node, ...props }: any) => <ul className="list-disc pl-6 my-4 space-y-2 marker:text-accent" {...props} />,
    ol: ({ node, ...props }: any) => <ol className="list-decimal pl-6 my-4 space-y-2 marker:text-accent font-medium" {...props} />,
    li: ({ node, ...props }: any) => <li className="text-foreground leading-relaxed" {...props} />,
    a: ({ node, ...props }: any) => {
      if (props.href === '#citation') {
        return <CitationBadge text={props.children?.toString() || ''} onCitationClick={onCitationClick} sources={sources} />
      }
      return <a className="text-accent hover:underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />
    }
  }
  
  const [isPlayingNew, setIsPlayingNew] = useState(false)
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  
  const handleTTS = async (e: React.MouseEvent) => {
    e.preventDefault();
    console.log("[DEBUG-TTS] --- handleTTS Triggered ---");
    console.log("[DEBUG-TTS] message_id:", message_id);
    console.log("[DEBUG-TTS] audioUrl state:", audioUrl);
    console.log("[DEBUG-TTS] audioRef.current:", !!audioRef.current);
    console.log("[DEBUG-TTS] isPlayingNew:", isPlayingNew);
    
    try {
      if (!message_id) {
         console.warn("[DEBUG-TTS] Aborting: No message_id");
         return
      }
      
      // Toggle play/pause if already loaded
      if (audioUrl && audioRef.current) {
         console.log("[DEBUG-TTS] Toggling existing audio");
         if (isPlayingNew) {
            audioRef.current.pause()
            setIsPlayingNew(false)
         } else {
            audioRef.current.play()
            setIsPlayingNew(true)
         }
         return
      }
      
      console.log("[DEBUG-TTS] Calling setIsGeneratingAudio(true)...");
      setIsGeneratingAudio(true)
      
      console.log("[DEBUG-TTS] Calling ChatService.generateMessageAudio...");
      const lang = detectedLanguage || (isArabic ? 'ar' : 'en');
      console.log("[DEBUG-TTS] Language selected:", lang);
      
      const url = await ChatService.generateMessageAudio(message_id, lang)
      console.log("[DEBUG-TTS] SUCCESS! Received URL:", url);
      
      setAudioUrl(url)
      
      console.log("[DEBUG-TTS] Creating new Audio object...");
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => {
          console.log("[DEBUG-TTS] Audio ended natively");
          setIsPlayingNew(false)
      }
      console.log("[DEBUG-TTS] Playing audio...");
      audio.play()
      setIsPlayingNew(true)
      console.log("[DEBUG-TTS] Flow complete.");
    } catch (err) {
      console.error("[DEBUG-TTS] FATAL ERROR in handleTTS:", err)
    } finally {
      setIsGeneratingAudio(false)
      console.log("[DEBUG-TTS] Finally block executed.");
    }
  }

  const msgRef = useRef<HTMLDivElement>(null)
  const prevTypingRef = useRef(isTyping)

  useEffect(() => {
    if (prevTypingRef.current && !isTyping) {
      // Transitioned from typing to finished - scroll to top of this message smoothly
      msgRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    prevTypingRef.current = isTyping
  }, [isTyping])

  useEffect(() => {
    if (audioBase64 && !audioRef.current) {
      const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`)
      audio.onended = () => setIsPlaying(false)
      audioRef.current = audio
    }
  }, [audioBase64])

  const toggleAudio = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setIsPlaying(false)
    } else {
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  // Transform raw text citations [Doc.pdf, Page 13] into markdown links for custom rendering
  const formattedContent = content.replace(/\[([^\]]+?),\s*(Page\s*\d+)\]/gi, '[$1 $2](#citation)')

  if (!isAI) {
    return (
      <div className="w-full py-4 flex justify-end animate-in fade-in slide-in-from-bottom-2">
        <div className="max-w-[85%] md:max-w-[70%] bg-neutral-100 rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-sm border border-black/5">
          <div dir={isArabic ? 'rtl' : 'ltr'} className={cn("text-foreground whitespace-pre-wrap leading-relaxed text-[15px]", isArabic && "font-arabic")}>
            {content}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div ref={msgRef} className="w-full py-6 flex justify-start animate-in fade-in slide-in-from-bottom-2">
      <div className="flex gap-4 w-full">
        {/* Avatar */}
        <div className="flex-shrink-0 mt-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm border border-border/50">
            <Network className="h-4 w-4 text-accent" />
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col w-full min-w-0">
          <span className="text-sm font-bold tracking-tight text-foreground mb-1">ASKME</span>
          
          {isTyping && content.length === 0 ? (
            <LoadingIndicator />
          ) : (
            <div className="w-full">
              <div 
                dir={isArabic ? 'rtl' : 'ltr'} 
                className={cn(
                  "prose prose-sm md:prose-base max-w-none break-words text-foreground relative",
                  isArabic && "font-arabic"
                )}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {formattedContent}
                </ReactMarkdown>
                {/* Streaming cursor effect */}
                {isTyping && content.length > 0 && (
                  <span className="inline-block w-1.5 h-4 ml-1 bg-accent animate-pulse align-middle" />
                )}
              </div>

              {/* Feedback buttons */}
              {content !== 'Unable to generate response. Please try again.' && (
                <div className="flex items-center gap-2 mt-4 pt-4 text-neutral-400">
                  {message_id && (
                    <button 
                      onClick={handleTTS}
                      disabled={isGeneratingAudio}
                      className="px-2 py-1.5 hover:text-accent hover:bg-accent/10 rounded transition-colors flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
                    >
                      {isGeneratingAudio ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : isPlayingNew ? (
                        <Square className="w-3.5 h-3.5 fill-current" />
                      ) : (
                        <Volume2 className="w-3.5 h-3.5" />
                      )} 
                      {isPlayingNew ? 'Stop' : 'Play'}
                    </button>
                  )}
                  <div className="w-px h-4 bg-border mx-1"></div>
                  <button className="p-1.5 hover:text-accent hover:bg-accent/10 rounded transition-colors"><ThumbsUp className="w-4 h-4" /></button>
                  <button className="p-1.5 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"><ThumbsDown className="w-4 h-4" /></button>
                  <div className="w-px h-4 bg-border mx-1"></div>
                  <button 
                    onClick={() => navigator.clipboard.writeText(content)}
                    className="px-2 py-1.5 hover:text-foreground hover:bg-neutral-100 rounded transition-colors flex items-center gap-1.5 text-xs font-medium"
                  >
                    <Copy className="w-3.5 h-3.5" /> Copy
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Audio Player */}
          {audioBase64 && !isTyping && (
            <div className="mt-6 flex items-center gap-3 rounded border border-border bg-white p-2 w-fit">
              <button 
                onClick={toggleAudio}
                className="flex h-8 w-8 items-center justify-center rounded-sm bg-accent text-primary transition-colors hover:bg-accent-hover"
              >
                {isPlaying ? <Square className="h-3 w-3 fill-current" /> : <Play className="h-3 w-3 fill-current ml-0.5" />}
              </button>
              <div className="flex flex-col pr-4">
                <span className="text-xs font-semibold uppercase text-foreground">Vocal Synthesis</span>
                <span className="text-[10px] uppercase text-neutral-dark">
                  {detectedLanguage === 'ar' ? 'Arabic' : 'English'}
                </span>
              </div>
              <div className="flex items-center gap-0.5 ml-2 h-4 pr-2">
                {[...Array(8)].map((_, i) => (
                  <div 
                    key={i} 
                    className={cn(
                      "w-0.5 bg-neutral-dark/40 transition-all",
                      isPlaying ? "animate-pulse bg-accent" : "h-1"
                    )}
                    style={{ 
                      height: isPlaying ? `${Math.max(30, Math.random() * 100)}%` : '4px',
                      animationDelay: `${i * 75}ms` 
                    }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

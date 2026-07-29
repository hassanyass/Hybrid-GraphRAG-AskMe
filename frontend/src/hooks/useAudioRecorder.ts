import { useState, useRef, useCallback } from 'react'

export function useAudioRecorder(onTranscriptChange?: (text: string) => void) {
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const recognitionRef = useRef<any>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async (language: string = 'en') => {
    // 1. Try Web Speech API for live STT
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = language === 'ar' ? 'ar-SA' : 'en-US'
        
        recognition.onresult = (event: any) => {
          let currentTranscript = ''
          for (let i = 0; i < event.results.length; i++) {
             currentTranscript += event.results[i][0].transcript
          }
          if (onTranscriptChange) {
            onTranscriptChange(currentTranscript)
          }
        }
        
        recognition.onerror = (event: any) => {
          console.error('Speech recognition error', event.error)
          stopRecording()
        }
        
        recognition.onend = () => {
          setIsRecording(false)
        }
        
        recognitionRef.current = recognition
        recognition.start()
        setIsRecording(true)
        setAudioBlob(null)
        return
      } catch (err) {
        console.warn("Speech recognition failed to start, falling back to MediaRecorder", err)
      }
    }
    
    // 2. Fallback to MediaRecorder Blob capture
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        // Clean up stream tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setAudioBlob(null)
    } catch (err) {
      console.error('Error accessing microphone:', err)
    }
  }, [onTranscriptChange])

  const stopRecording = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop()
      setIsRecording(false)
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }, [isRecording])

  const cancelRecording = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop()
      setIsRecording(false)
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setAudioBlob(null)
    }
  }, [isRecording])

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    cancelRecording,
    clearAudio: () => setAudioBlob(null)
  }
}

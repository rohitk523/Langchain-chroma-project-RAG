'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Send, Bot, User, FileText, Loader2 } from 'lucide-react'
import { ChatMessage, useChat } from '@/hooks/use-chat'
import { toast } from 'sonner'

interface ChatInterfaceProps {
  chatId: string | null
  onChatCreated: (chatId: string) => void
}

export function ChatInterface({ chatId, onChatCreated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { sendMessage, getChatHistory } = useChat()

  // Load chat history when chatId changes
  useEffect(() => {
    if (chatId) {
      setLoadingHistory(true)
      getChatHistory(chatId)
        .then(setMessages)
        .finally(() => setLoadingHistory(false))
    } else {
      setMessages([])
    }
  }, [chatId, getChatHistory])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendMessage(userMessage, chatId)
      
      if (response) {
        // If this was a new chat, notify parent
        if (!chatId) {
          onChatCreated(response.chat_id)
        }

        // Add user message and AI response to local state
        const newUserMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          chat_id: response.chat_id,
          user_id: '',
          message: userMessage,
          response: '',
          message_type: 'user',
          sources: [],
          timestamp: new Date().toISOString(),
          metadata: {}
        }

        const newAiMessage: ChatMessage = {
          id: `ai-${Date.now()}`,
          chat_id: response.chat_id,
          user_id: '',
          message: '',
          response: response.response,
          message_type: 'assistant',
          sources: response.sources,
          timestamp: response.timestamp,
          metadata: {}
        }

        setMessages(prev => [...prev, newUserMessage, newAiMessage])
      }
    } catch {
      toast.error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.message_type === 'user'
    const content = isUser ? message.message : message.response
    
    return (
      <div key={`${message.id}-${index}`} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
          <div className="flex items-center mb-1">
            <div className={`flex items-center space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`p-1 rounded-full ${isUser ? 'bg-blue-500' : 'bg-gray-500'}`}>
                {isUser ? (
                  <User className="h-3 w-3 text-white" />
                ) : (
                  <Bot className="h-3 w-3 text-white" />
                )}
              </div>
              <span className="text-xs text-gray-500">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
          </div>
          
          <Card className={`${isUser ? 'bg-blue-500 text-white' : 'bg-white'}`}>
            <CardContent className="p-3">
              <p className="text-sm whitespace-pre-wrap">{content}</p>
              
              {/* Sources for AI messages */}
              {!isUser && message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center mb-2">
                    <FileText className="h-4 w-4 text-gray-500 mr-1" />
                    <span className="text-xs font-medium text-gray-700">Sources</span>
                  </div>
                  <div className="space-y-2">
                    {message.sources.map((source, sourceIndex) => (
                      <div key={sourceIndex} className="p-2 bg-gray-50 rounded text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <Badge variant="outline" className="text-xs">
                            {Math.round(source.similarity_score * 100)}% match
                          </Badge>
                          {(() => {
                            const pageNum = source.metadata.page;
                            return pageNum && typeof pageNum === 'number' ? (
                              <span className="text-gray-500">
                                Page {pageNum}
                              </span>
                            ) : null;
                          })()}
                        </div>
                        <p className="text-gray-700">{String(source.content)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
          {loadingHistory ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <Bot className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p className="text-lg font-medium">Start a conversation</p>
                <p className="text-sm text-gray-400 mt-1">
                  Ask questions about your uploaded documents
                </p>
              </div>
            </div>
          ) : (
            <div>
              {messages.map((message, index) => renderMessage(message, index))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <div className="flex space-x-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your documents..."
            className="flex-1 min-h-[40px] max-h-[120px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="lg"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
} 
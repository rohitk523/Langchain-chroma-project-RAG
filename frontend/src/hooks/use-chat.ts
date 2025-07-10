import { useState, useEffect, useCallback } from 'react'
// import { useAuth } from '@clerk/nextjs'
import axios from 'axios'
import { toast } from 'sonner'

export interface ChatMessage {
  id: string
  chat_id: string
  user_id: string
  message: string
  response: string
  message_type: string
  sources: Array<{
    content: string
    metadata: Record<string, unknown>
    similarity_score: number
  }>
  timestamp: string
  metadata: Record<string, unknown>
}

export interface Chat {
  chat_id: string
  title: string
  created_at: string
  last_message_at: string
  message_count: number
}

export interface ChatResponse {
  response: string
  chat_id: string
  sources: Array<{
    content: string
    metadata: Record<string, unknown>
    similarity_score: number
  }>
  timestamp: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useChat() {
  // const { getToken } = useAuth()
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Mock auth function for testing
  const getAuthHeaders = useCallback(async () => {
    // const token = await getToken()
    return {
      // Authorization: `Bearer ${token}`,
      Authorization: `Bearer mock-token`,
      'Content-Type': 'application/json',
    }
  }, [])

  const fetchChats = useCallback(async () => {
    try {
      setLoading(true)
      const headers = await getAuthHeaders()
      const response = await axios.get(`${API_URL}/api/chats`, { headers })
      setChats(response.data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch chats:', err)
      setError('Failed to load chats')
      toast.error('Failed to load chats')
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders])

  const sendMessage = useCallback(async (
    message: string,
    chatId?: string | null
  ): Promise<ChatResponse | null> => {
    try {
      const headers = await getAuthHeaders()
      const response = await axios.post(
        `${API_URL}/api/chat`,
        {
          message,
          chat_id: chatId,
          include_sources: true,
        },
        { headers }
      )
      
      // Refresh chats after sending a message
      await fetchChats()
      
      return response.data
    } catch (err) {
      console.error('Failed to send message:', err)
      toast.error('Failed to send message')
      return null
    }
  }, [getAuthHeaders, fetchChats])

  const getChatHistory = useCallback(async (chatId: string): Promise<ChatMessage[]> => {
    try {
      const headers = await getAuthHeaders()
      const response = await axios.get(
        `${API_URL}/api/chat/${chatId}/history`,
        { headers }
      )
      return response.data
    } catch (err) {
      console.error('Failed to fetch chat history:', err)
      toast.error('Failed to load chat history')
      return []
    }
  }, [getAuthHeaders])

  const deleteChat = useCallback(async (chatId: string): Promise<boolean> => {
    try {
      const headers = await getAuthHeaders()
      await axios.delete(`${API_URL}/api/chat/${chatId}`, { headers })
      
      // Remove from local state
      setChats(prev => prev.filter(chat => chat.chat_id !== chatId))
      toast.success('Chat deleted successfully')
      return true
    } catch (err) {
      console.error('Failed to delete chat:', err)
      toast.error('Failed to delete chat')
      return false
    }
  }, [getAuthHeaders])

  const uploadDocument = useCallback(async (file: File): Promise<boolean> => {
    try {
      const headers = await getAuthHeaders()
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { 'Content-Type': _, ...uploadHeaders } = headers // Let browser set multipart boundary
      
      const formData = new FormData()
      formData.append('file', file)
      
      await axios.post(`${API_URL}/api/upload`, formData, { 
        headers: {
          Authorization: uploadHeaders.Authorization,
        }
      })
      
      toast.success('Document uploaded successfully')
      return true
    } catch (err) {
      console.error('Failed to upload document:', err)
      toast.error('Failed to upload document')
      return false
    }
  }, [getAuthHeaders])

  const refetchChats = useCallback(() => {
    fetchChats()
  }, [fetchChats])

  useEffect(() => {
    fetchChats()
  }, [fetchChats])

  return {
    chats,
    loading,
    error,
    sendMessage,
    getChatHistory,
    deleteChat,
    uploadDocument,
    refetchChats,
  }
} 
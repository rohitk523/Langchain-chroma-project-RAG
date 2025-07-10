'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'
import { MessageSquare, MoreVertical, Trash2, Loader2 } from 'lucide-react'
import { Chat, useChat } from '@/hooks/use-chat'
import { toast } from 'sonner'

interface ChatSidebarProps {
  chats: Chat[]
  currentChatId: string | null
  onSelectChat: (chatId: string) => void
  loading: boolean
}

export function ChatSidebar({ 
  chats, 
  currentChatId, 
  onSelectChat, 
  loading 
}: ChatSidebarProps) {
  const [deletingChatId, setDeletingChatId] = useState<string | null>(null)
  const { deleteChat } = useChat()

  const handleDeleteChat = async (chatId: string) => {
    setDeletingChatId(chatId)
    try {
      const success = await deleteChat(chatId)
      if (success && currentChatId === chatId) {
        // If we deleted the current chat, reset to no chat
        onSelectChat('')
      }
    } catch {
      toast.error('Failed to delete chat')
    } finally {
      setDeletingChatId(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    )
  }

  if (chats.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <MessageSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
        <p className="text-sm">No chats yet</p>
        <p className="text-xs text-gray-400 mt-1">
          Start a new conversation or upload a document
        </p>
      </div>
    )
  }

  // Sort chats by last message date (most recent first)
  const sortedChats = [...chats].sort((a, b) => 
    new Date(b.last_message_at).getTime() - new Date(a.last_message_at).getTime()
  )

  return (
    <ScrollArea className="h-full p-2">
      <div className="space-y-2">
        {sortedChats.map((chat) => (
          <Card 
            key={chat.chat_id}
            className={`cursor-pointer transition-colors hover:bg-gray-50 ${
              currentChatId === chat.chat_id 
                ? 'ring-2 ring-blue-500 bg-blue-50' 
                : ''
            }`}
            onClick={() => onSelectChat(chat.chat_id)}
          >
            <CardContent className="p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {chat.title}
                    </h3>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      {formatDate(chat.last_message_at)}
                    </p>
                    <Badge variant="secondary" className="text-xs">
                      {chat.message_count}
                    </Badge>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 ml-2"
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                    >
                      {deletingChatId === chat.chat_id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <MoreVertical className="h-3 w-3" />
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteChat(chat.chat_id)
                      }}
                      className="text-red-600 focus:text-red-600"
                      disabled={deletingChatId === chat.chat_id}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Chat
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  )
} 
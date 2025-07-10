'use client'

import { useState } from 'react'
import { UserButton } from '@clerk/nextjs'
import { ChatInterface } from '@/components/chat/chat-interface'
import { ChatSidebar } from '@/components/chat/chat-sidebar'
import { DocumentUpload } from '@/components/chat/document-upload'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Plus, Upload } from 'lucide-react'
import { useChat } from '@/hooks/use-chat'

export default function DashboardPage() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  
  const { chats, loading: chatsLoading, refetchChats } = useChat()

  const handleNewChat = () => {
    setCurrentChatId(null)
  }

  const handleSelectChat = (chatId: string) => {
    setCurrentChatId(chatId)
  }

  const handleUploadSuccess = () => {
    setIsUploadDialogOpen(false)
    // Optionally refetch chats or show success message
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden border-r bg-white`}>
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-semibold">RAG Chat</h1>
              <UserButton afterSignOutUrl="/" />
            </div>
            
            <div className="space-y-2">
              <Button 
                onClick={handleNewChat}
                className="w-full justify-start"
                variant="outline"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Chat
              </Button>
              
              <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="w-full justify-start"
                    variant="outline"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Document
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Upload PDF Document</DialogTitle>
                  </DialogHeader>
                  <DocumentUpload onUploadSuccess={handleUploadSuccess} />
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-hidden">
            <ChatSidebar
              chats={chats}
              currentChatId={currentChatId}
              onSelectChat={handleSelectChat}
              loading={chatsLoading}
            />
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b bg-white flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            ☰
          </Button>
          
          <h2 className="font-medium text-gray-900">
            {currentChatId ? 'Chat Session' : 'New Chat'}
          </h2>
          
          <div className="w-8" /> {/* Spacer for center alignment */}
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            chatId={currentChatId}
            onChatCreated={(newChatId: string) => {
              setCurrentChatId(newChatId)
              refetchChats()
            }}
          />
        </div>
      </div>
    </div>
  )
} 
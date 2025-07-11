'use client'

import { useState } from 'react'
import { UserButton, useAuth } from '@clerk/nextjs'
import { ChatInterface } from '@/components/chat/chat-interface'
import { ChatSidebar } from '@/components/chat/chat-sidebar'
import { DocumentUpload } from '@/components/chat/document-upload'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Plus, Upload, Key, Copy } from 'lucide-react'
import { useChat } from '@/hooks/use-chat'
import { toast } from 'sonner'

export default function DashboardPage() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [isTokenDialogOpen, setIsTokenDialogOpen] = useState(false)
  const [token, setToken] = useState<string>('')
  
  const { chats, loading: chatsLoading, refetchChats } = useChat()
  const { getToken } = useAuth()

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

  const handleGetToken = async () => {
    try {
      const authToken = await getToken()
      if (authToken) {
        setToken(authToken)
        setIsTokenDialogOpen(true)
        console.log('Clerk Token:', authToken)
        toast.success('Token retrieved successfully!')
      } else {
        toast.error('No token available')
      }
    } catch (error) {
      console.error('Error getting token:', error)
      toast.error('Failed to get token')
    }
  }

  const handleCopyToken = () => {
    navigator.clipboard.writeText(token)
    toast.success('Token copied to clipboard!')
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
              <UserButton />
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

              <Button 
                onClick={handleGetToken}
                className="w-full justify-start"
                variant="outline"
              >
                <Key className="w-4 h-4 mr-2" />
                Get Token
              </Button>

              <Dialog open={isTokenDialogOpen} onOpenChange={setIsTokenDialogOpen}>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Clerk Authentication Token</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-2">
                        Use this token for testing API endpoints in Swagger UI:
                      </p>
                      <code className="block bg-white p-2 rounded border text-xs break-all">
                        {token}
                      </code>
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button 
                        onClick={handleCopyToken}
                        variant="outline"
                        size="sm"
                      >
                        <Copy className="w-4 h-4 mr-1" />
                        Copy Token
                      </Button>
                      <Button 
                        onClick={() => setIsTokenDialogOpen(false)}
                        size="sm"
                      >
                        Close
                      </Button>
                    </div>
                  </div>
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
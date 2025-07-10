// import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">RAG Chat</h1>
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <Button variant="default">Dashboard</Button>
            </Link>
            <Button variant="default">Sign In (Temp)</Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-6">
            AI-Powered Document Chat
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Upload your documents and chat with them using advanced AI. 
            Get instant answers from your PDFs with source citations.
          </p>

          <div className="mb-12">
            <Link href="/dashboard">
              <Button size="lg" className="px-8 py-4 text-lg">
                Go to Dashboard
              </Button>
            </Link>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  📄 Document Upload
                </CardTitle>
                <CardDescription>
                  Upload PDF documents and we&apos;ll process them for intelligent search
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Supports PDF files up to 10MB with automatic text extraction and chunking
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  💬 Smart Chat
                </CardTitle>
                <CardDescription>
                  Ask questions about your documents and get accurate answers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Powered by advanced AI with context-aware responses and source citations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  📚 Chat History
                </CardTitle>
                <CardDescription>
                  Access your previous conversations and continue where you left off
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  All your chats are saved and searchable for easy reference
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

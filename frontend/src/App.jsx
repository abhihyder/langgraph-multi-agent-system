import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAuth } from './contexts/AuthContext'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Markdown components with syntax highlighting
const MarkdownComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    const language = match ? match[1] : ''
    
    return !inline ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language}
        PreTag="div"
        className="code-block"
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code className="inline-code" {...props}>
        {children}
      </code>
    )
  },
  p({ children }) {
    return <p className="markdown-paragraph">{children}</p>
  },
  h1({ children }) {
    return <h1 className="markdown-h1">{children}</h1>
  },
  h2({ children }) {
    return <h2 className="markdown-h2">{children}</h2>
  },
  h3({ children }) {
    return <h3 className="markdown-h3">{children}</h3>
  },
  ul({ children }) {
    return <ul className="markdown-list">{children}</ul>
  },
  ol({ children }) {
    return <ol className="markdown-list">{children}</ol>
  },
  li({ children }) {
    return <li className="markdown-list-item">{children}</li>
  },
  blockquote({ children }) {
    return <blockquote className="markdown-blockquote">{children}</blockquote>
  },
  a({ href, children }) {
    return <a href={href} className="markdown-link" target="_blank" rel="noopener noreferrer">{children}</a>
  },
  table({ children }) {
    return <table className="markdown-table">{children}</table>
  }
}

function App() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState(null)
  const messagesEndRef = useRef(null)

  // Check API health on mount
  useEffect(() => {
    checkApiHealth()
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`)
      setApiStatus(response.data)
    } catch (error) {
      console.error('API health check failed:', error)
      setApiStatus({ status: 'error', api_key_configured: false })
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    
    if (!inputMessage.trim() || isLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    
    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      const response = await axios.post(`${API_URL}/api/query`, {
        query: userMessage,
        context: {},
        verbose: true
      })

      const rawContent =
        response?.data?.response ??
        response?.data?.message ??
        response?.data

      const aiContent =
        typeof rawContent === 'string'
          ? rawContent
          : rawContent
          ? JSON.stringify(rawContent, null, 2)
          : 'I was unable to generate a response. Please try again.'

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: aiContent,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        role: 'error',
        content:
          error.response?.data?.detail ||
          error.response?.data?.message ||
          'Failed to get response from AI. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <div className="app">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <h1>🤖 Agentic AI Chat</h1>
            <p>Powered by Multi-Agent System</p>
          </div>
          <div className="header-actions">
            {user && (
              <div className="user-profile">
                {user.picture && (
                  <img src={user.picture} alt={user.name ?? 'User avatar'} className="user-avatar" />
                )}
                <div className="user-info">
                  <span className="user-name">{user.name || user.email}</span>
                  <button onClick={logout} className="logout-btn" title="Logout">
                    🚪 Logout
                  </button>
                </div>
              </div>
            )}
            {apiStatus && (
              <span
                className={`status-badge ${
                  apiStatus.status === 'ok' || apiStatus.status === 'healthy'
                    ? 'ok'
                    : 'error'
                }`}
              >
                {apiStatus.api_key_configured ? '🟢 Connected' : '🔴 API Key Missing'}
              </span>
            )}
            <button onClick={clearChat} className="clear-btn" title="Clear chat">
              🗑️
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>👋 Welcome to Agentic AI!</h2>
              <p>Ask me anything. I'll route your question to specialized agents:</p>
              <div className="agent-cards">
                <div className="agent-card">
                  <span className="agent-icon">🔍</span>
                  <strong>Research Agent</strong>
                  <p>Facts & Analysis</p>
                </div>
                <div className="agent-card">
                  <span className="agent-icon">✍️</span>
                  <strong>Writing Agent</strong>
                  <p>Content Creation</p>
                </div>
                <div className="agent-card">
                  <span className="agent-icon">💻</span>
                  <strong>Code Agent</strong>
                  <p>Code Generation</p>
                </div>
              </div>
              <div className="example-queries">
                <p><strong>Try asking:</strong></p>
                <div className="query-chips">
                  <span onClick={() => setInputMessage("What is Docker?")}>What is Docker?</span>
                  <span onClick={() => setInputMessage("Write a tutorial on Python")}>Write a tutorial on Python</span>
                  <span onClick={() => setInputMessage("Create a REST API in FastAPI")}>Create a REST API in FastAPI</span>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : message.role === 'error' ? '⚠️' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-text">
                  {message.role === 'user' || message.role === 'error' ? (
                    message.content
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={MarkdownComponents}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>
                <div className="message-timestamp">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form className="input-container" onSubmit={sendMessage}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

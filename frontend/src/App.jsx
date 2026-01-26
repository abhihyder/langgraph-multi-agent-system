import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
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
      // Call API
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: userMessage,
        verbose: true
      })

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        role: 'error',
        content: error.response?.data?.detail || 'Failed to get response from AI. Please try again.',
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
            {apiStatus && (
              <span className={`status-badge ${apiStatus.status}`}>
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
                <div className="message-text">{message.content}</div>
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

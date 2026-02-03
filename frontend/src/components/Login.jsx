import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Login.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Check if we're returning from OAuth callback with token and user data
  useEffect(() => {
    const token = searchParams.get('token')
    const userJson = searchParams.get('user')
    const error = searchParams.get('error')

    if (error) {
      alert(`Login failed: ${error}`)
      return
    }

    if (token && userJson) {
      try {
        const user = JSON.parse(userJson)
        
        // Store token in cookie
        const expirationDays = 7 // Match JWT expiration
        const expires = new Date()
        expires.setDate(expires.getDate() + expirationDays)
        document.cookie = `access_token=${token}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`
        
        // Store user info in cookie for display
        document.cookie = `user_data=${encodeURIComponent(JSON.stringify(user))}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`
        
        // Update auth context
        login(user, token)
        
        // Navigate to home
        navigate('/', { replace: true })
      } catch (err) {
        console.error('Failed to parse user data:', err)
        alert('Login failed: Invalid response data')
      }
    }
  }, [searchParams, navigate, login])

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleGoogleLogin = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = `${API_URL}/auth/google/login`
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="logo">🤖</div>
          <h1>Agentic AI Chat</h1>
          <p>Multi-Agent AI System</p>
        </div>

        <div className="login-content">
          <h2>Welcome</h2>
          <p className="login-subtitle">
            Sign in to access your personalized AI assistant
          </p>

          <button 
            className="google-login-btn"
            onClick={handleGoogleLogin}
          >
            <svg className="google-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="login-features">
            <h3>Features</h3>
            <ul>
              <li>🎯 Intelligent query routing</li>
              <li>📝 Research, writing, and code assistance</li>
              <li>💡 Context-aware responses</li>
              <li>🔒 Secure and private</li>
            </ul>
          </div>
        </div>

        <div className="login-footer">
          <p>By signing in, you agree to our Terms of Service and Privacy Policy</p>
        </div>
      </div>
    </div>
  )
}

export default Login

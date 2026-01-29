import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Helper to get cookie value
const getCookie = (name) => {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
  return null
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getCookie('access_token')
      const userDataCookie = getCookie('user_data')
      
      if (!token || !userDataCookie) {
        setLoading(false)
        return
      }

      try {
        // Set Authorization header with token
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        // Parse user data from cookie
        const userData = JSON.parse(decodeURIComponent(userDataCookie))
        
        // Verify token is still valid by fetching profile
        const response = await axios.get(`${API_URL}/api/user/profile`)
        setUser(response.data)
      } catch (error) {
        console.error('Auth check failed:', error)
        // Token is invalid, clear everything
        delete axios.defaults.headers.common['Authorization']
        clearCookies()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const clearCookies = () => {
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
    document.cookie = 'user_data=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
  }

  const login = (userData, token) => {
    // Set Authorization header for all subsequent requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    setUser(userData)
  }

  const logout = async () => {
    try {
      // Call backend logout endpoint
      await axios.post(`${API_URL}/auth/logout`)
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear cookies and auth header
      clearCookies()
      delete axios.defaults.headers.common['Authorization']
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    login,
    logout,
    setAuth: login, // Alias for consistency
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

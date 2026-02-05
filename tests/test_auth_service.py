"""
Unit Tests for AuthService
Testing authentication, token management, and user operations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.auth_service import AuthService


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test suite for AuthService"""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance"""
        return AuthService()
    
    @patch('app.services.auth_service.Flow.from_client_config')
    def test_create_oauth_flow(self, mock_flow_class, auth_service):
        """Test OAuth flow creation"""
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        flow = auth_service._create_oauth_flow()
        
        assert flow is not None
        mock_flow_class.assert_called_once()
    
    @patch('app.services.auth_service.Flow.from_client_config')
    def test_get_authorization_url(self, mock_flow_class, auth_service):
        """Test getting Google OAuth authorization URL"""
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?...",
            "state_value"
        )
        mock_flow_class.return_value = mock_flow
        
        url = auth_service.get_authorization_url(state="test_state")
        
        assert "https://accounts.google.com" in url
        mock_flow.authorization_url.assert_called_once()
    
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.Flow.from_client_config')
    def test_verify_google_token_success(self, mock_flow_class, mock_verify, auth_service):
        """Test successful Google token verification"""
        # Mock flow and credentials
        mock_flow = Mock()
        mock_credentials = Mock()
        mock_credentials.id_token = "test_token"
        mock_flow.credentials = mock_credentials
        mock_flow_class.return_value = mock_flow
        
        # Mock token verification
        mock_verify.return_value = {
            "sub": "google_user_123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg"
        }
        
        result = auth_service._verify_google_token("auth_code")
        
        assert result["google_id"] == "google_user_123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        mock_flow.fetch_token.assert_called_once_with(code="auth_code")
    
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.Flow.from_client_config')
    def test_verify_google_token_failure(self, mock_flow_class, mock_verify, auth_service):
        """Test Google token verification failure"""
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        # Mock verification failure
        mock_verify.side_effect = ValueError("Invalid token")
        
        with pytest.raises(ValueError):
            auth_service._verify_google_token("invalid_code")
    


@pytest.mark.unit
@pytest.mark.auth
class TestJWTSecurity:
    """Test JWT token generation and validation"""
    
    @patch('app.utils.auth.security.jwt.encode')
    def test_token_creation_with_expiration(self, mock_encode):
        """Test JWT token includes expiration"""
        from app.utils.auth.security import create_access_token
        
        mock_encode.return_value = "encoded_token"
        
        token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(hours=1)
        )
        
        assert token == "encoded_token"
        mock_encode.assert_called_once()
    
    @patch('app.utils.auth.security.jwt.decode')
    def test_token_validation_success(self, mock_decode):
        """Test successful JWT token validation"""
        from app.utils.auth.security import verify_access_token
        
        mock_decode.return_value = {
            "sub": "test@example.com",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
        }
        
        payload = verify_access_token("valid_token")
        
        assert payload["sub"] == "test@example.com"
    
    @patch('app.utils.auth.security.jwt.decode')
    def test_token_validation_expired(self, mock_decode):
        """Test expired JWT token validation"""
        from app.utils.auth.security import verify_access_token
        from jose.exceptions import ExpiredSignatureError
        
        mock_decode.side_effect = ExpiredSignatureError()
        
        with pytest.raises(ExpiredSignatureError):
            verify_access_token("expired_token")
    
    @patch('app.utils.auth.security.jwt.decode')
    def test_token_validation_invalid(self, mock_decode):
        """Test invalid JWT token validation"""
        from app.utils.auth.security import verify_access_token
        from jose.exceptions import JWTError
        
        mock_decode.side_effect = JWTError()
        
        with pytest.raises(JWTError):
            verify_access_token("invalid_token")


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Integration tests for complete authentication flow"""
    
    @patch('app.services.auth_service.Flow.from_client_config')
    def test_complete_google_oauth_flow(self, mock_flow_class):
        """Test complete Google OAuth authorization URL generation"""
        # Setup mocks
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test",
            "state_token"
        )
        mock_flow_class.return_value = mock_flow
        
        # Execute flow
        auth_service = AuthService()
        
        # Get authorization URL
        auth_url = auth_service.get_authorization_url()
        assert "https://accounts.google.com" in auth_url


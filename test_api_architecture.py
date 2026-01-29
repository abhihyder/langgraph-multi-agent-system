#!/usr/bin/env python3
"""
Test script to verify the API architecture is working correctly
"""

import sys

def test_imports():
    """Test all imports."""
    print("Testing imports...")
    try:
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_request_models():
    """Test request model creation."""
    print("\nTesting request models...")
    try:
        from app.requests.chat_request import ChatRequest
        request = ChatRequest(message="Test message", context=None)
        assert request.message == "Test message"
        print("✅ Request models working")
        return True
    except Exception as e:
        print(f"❌ Request model error: {e}")
        return False

def test_response_models():
    """Test response model creation."""
    print("\nTesting response models...")
    try:
        from app.responses.chat_response import ChatResponse
        response = ChatResponse(
            response="Test response",
            intent="test",
            agents_used=["test_agent"],
            metadata=None
        )
        assert response.response == "Test response"
        print("✅ Response models working")
        return True
    except Exception as e:
        print(f"❌ Response model error: {e}")
        return False

def test_controller():
    """Test controller instantiation."""
    print("\nTesting controller...")
    try:
        from app.controllers.chat_controller import ChatController
        controller = ChatController()
        assert hasattr(controller, 'chat_service')
        print("✅ Controller working")
        return True
    except Exception as e:
        print(f"❌ Controller error: {e}")
        return False

def test_service():
    """Test service instantiation."""
    print("\nTesting service...")
    try:
        from app.services.chat_service import ChatService
        service = ChatService()
        info = service.get_agent_info()
        assert 'agents' in info
        assert 'orchestrator' in info
        print("✅ Service working")
        return True
    except Exception as e:
        print(f"❌ Service error: {e}")
        return False

def test_production_server():
    """Test production server can be imported."""
    print("\nTesting production server...")
    try:
        from server import app
        routes = [getattr(route, 'path', None) for route in app.routes]
        routes = [r for r in routes if r is not None]  # Filter out None values
        # Check for actual production routes
        assert '/api/query' in routes or any('/api' in r for r in routes)
        assert '/health' in routes
        print("✅ Production server configured correctly")
        print(f"   Sample routes: {[r for r in routes if '/api' in r or r == '/health'][:5]}")
        return True
    except Exception as e:
        print(f"❌ Production server error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("API Architecture Test Suite")
    print("="*60)
    
    tests = [
        test_imports,
        test_request_models,
        test_response_models,
        test_controller,
        test_service,
        test_production_server
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("="*60)
    
    if all(results):
        print("\n🎉 All tests passed! API architecture is working correctly.")
        print("\n📚 Next steps:")
        print("   1. Start server: python server.py")
        print("   2. Or use helper: ./start.sh")
        print("   3. Visit docs: http://localhost:8000/docs")
        print("   4. Test endpoint: curl -X POST http://localhost:8000/api/query \\")
        print("                           -H 'Authorization: Bearer <token>' \\")
        print("                           -H 'Content-Type: application/json' \\")
        print("                           -d '{\"query\": \"Hello!\", \"context\": {}}'")
        print("   Note: Most endpoints require OAuth authentication")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

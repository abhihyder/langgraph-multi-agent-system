# FastAPI + React Chat UI - Setup Guide

## Quick Start

### 1. Backend Setup

```bash
# Install backend dependencies
pip install fastapi uvicorn

# Start the FastAPI server
python server.py
```

The backend will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: http://localhost:3000

## Usage

1. Start the backend server (Python)
2. Start the frontend development server (React)
3. Open http://localhost:3000 in your browser
4. Start chatting with the AI!

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/chat` - Send message to AI
- `GET /api/agents` - List available agents

## Example API Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Docker?"}'
```

## Features

✅ Real-time chat interface
✅ Multi-agent routing (Research, Writing, Code)
✅ Loading indicators
✅ Error handling
✅ Responsive design
✅ Message history
✅ Clear chat functionality
✅ Example queries
✅ API health monitoring

## Production Deployment

### Backend

```bash
# Using uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend

```bash
cd frontend
npm run build
# Deploy the 'dist' folder to your hosting service
```

## Environment Variables

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your-api-key-here
```

## Troubleshooting

**Backend not starting:**
- Check if port 8000 is available
- Verify OpenAI API key is set

**Frontend not connecting:**
- Verify backend is running on port 8000
- Check browser console for CORS errors

**Chat not working:**
- Verify API key in backend
- Check backend logs for errors
- Open browser DevTools Network tab

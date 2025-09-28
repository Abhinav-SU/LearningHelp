const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const axios = require('axios');
const expressWs = require('express-ws');
const WebSocket = require('ws');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

// Enable WebSocket support
expressWs(app);

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'ai-interview-backend',
    timestamp: new Date().toISOString()
  });
});

// F.0.1: TTS Endpoint - Text to Speech
app.post('/api/tts', async (req, res) => {
  try {
    const { text, voice = 'alloy', speed = 1.0 } = req.body;
    
    if (!text) {
      return res.status(400).json({ error: 'Text is required' });
    }

    console.log(`[TTS] Processing text: "${text.substring(0, 50)}..."`);

    // OpenAI TTS API call
    const response = await axios.post(
      'https://api.openai.com/v1/audio/speech',
      {
        model: 'tts-1',
        input: text,
        voice: voice,
        speed: speed
      },
      {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        responseType: 'arraybuffer'
      }
    );

    res.set({
      'Content-Type': 'audio/mpeg',
      'Content-Length': response.data.length
    });
    
    res.send(response.data);
    console.log('[TTS] Audio generated successfully');

  } catch (error) {
    console.error('[TTS] Error:', error.response?.data || error.message);
    res.status(500).json({ 
      error: 'TTS generation failed',
      details: error.response?.data || error.message 
    });
  }
});

// F.0.2: LLM Q&A Endpoint
app.post('/api/llm/question', async (req, res) => {
  try {
    const { question, context = '' } = req.body;
    
    if (!question) {
      return res.status(400).json({ error: 'Question is required' });
    }

    console.log(`[LLM] Processing question: "${question}"`);

    // Forward to Python microservice for LLM processing
    const response = await axios.post(
      `${process.env.PYTHON_SERVICE_URL}/llm/answer`,
      {
        question,
        context
      }
    );

    console.log('[LLM] Answer generated successfully');
    res.json(response.data);

  } catch (error) {
    console.error('[LLM] Error:', error.response?.data || error.message);
    res.status(500).json({ 
      error: 'LLM processing failed',
      details: error.response?.data || error.message 
    });
  }
});

// F.0.3: Vector Search Endpoint
app.get('/api/vector/search', async (req, res) => {
  try {
    const { query, limit = 5 } = req.query;
    
    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    console.log(`[Vector] Searching for: "${query}"`);

    // Forward to Python microservice for vector search
    const response = await axios.get(
      `${process.env.PYTHON_SERVICE_URL}/vector/search`,
      {
        params: { query, limit }
      }
    );

    console.log(`[Vector] Found ${response.data.results?.length || 0} results`);
    res.json(response.data);

  } catch (error) {
    console.error('[Vector] Error:', error.response?.data || error.message);
    res.status(500).json({ 
      error: 'Vector search failed',
      details: error.response?.data || error.message 
    });
  }
});

// F.1.1: WebSocket Audio Proxy
app.ws('/ws/audio', (ws, req) => {
  console.log('🎤 WebSocket audio proxy connection established');
  
  let pythonWs = null;
  const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'ws://localhost:8001';
  
  // Connect to Python service WebSocket
  const connectToPython = () => {
    try {
      pythonWs = new WebSocket(`${pythonServiceUrl}/ws/stream/audio`);
      
      pythonWs.on('open', () => {
        console.log('✅ Connected to Python audio service');
      });
      
      pythonWs.on('message', (data) => {
        // Forward Python service messages to frontend
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });
      
      pythonWs.on('close', () => {
        console.log('❌ Python audio service connection closed');
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });
      
      pythonWs.on('error', (error) => {
        console.error('❌ Python audio service error:', error);
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });
      
    } catch (error) {
      console.error('❌ Failed to connect to Python service:', error);
      ws.close();
    }
  };
  
  // Handle messages from frontend
  ws.on('message', (data) => {
    // Forward audio data to Python service
    if (pythonWs && pythonWs.readyState === WebSocket.OPEN) {
      pythonWs.send(data);
    } else {
      console.log('⚠️ Python service not connected, attempting reconnection...');
      connectToPython();
    }
  });
  
  // Handle frontend disconnection
  ws.on('close', () => {
    console.log('🎤 Frontend audio connection closed');
    if (pythonWs) {
      pythonWs.close();
    }
  });
  
  ws.on('error', (error) => {
    console.error('❌ Frontend audio connection error:', error);
    if (pythonWs) {
      pythonWs.close();
    }
  });
  
  // Initial connection to Python service
  connectToPython();
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Backend server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🎤 WebSocket audio proxy: ws://localhost:${PORT}/ws/audio`);
});

module.exports = app;
# AI Interview System

## Development Philosophy
Increment, Test, Deploy, Deprecate. Every new feature must be tested against its own core checkpoint and the accumulated checkpoints of all previous pillars.

## Technical Stack
- **Frontend**: Next.js / ReactJS
- **Backend**: Node.js / Express + Python Microservices
- **LLM**: Cost-optimized, low-latency API (Gemini 2.5 Flash-Lite or GPT-4o mini)
- **ASR/TTS**: Streaming ASR API (OpenAI Realtime) + high-quality TTS (Microsoft Edge TTS/Cartesia)
- **Vector DB**: LanceDB (Embedded) - eliminates server costs for MVP

## Project Structure
```
├── frontend/          # Next.js React application
├── backend/           # Node.js Express API server
├── python-services/   # Python microservices for LLM/ASR/Vector DB
└── docs/             # Documentation and checkpoints
```

## Quick Start
```bash
# Install all dependencies
npm run install:all

# Start all services in development mode
npm run dev
```

## Current Development Phase
**Pillar 0: Foundational Connectivity and Static MVP (1-2 Weeks)**

### Checkpoints
- [ ] Checkpoint 0.1: Verify text → TTS → audio playback works
- [ ] Checkpoint 0.2: Test LLM responds correctly to technical questions  
- [ ] Checkpoint 0.3: Verify vector search returns expected documents

## API Endpoints
- `POST /api/tts` - Text-to-speech conversion
- `POST /api/llm/question` - LLM Q&A endpoint
- `GET /api/vector/search` - Vector similarity search
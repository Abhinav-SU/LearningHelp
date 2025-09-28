'use client';

import { useState } from 'react';

interface LLMResponse {
  answer: string;
  model_used: string;
  processing_time: number;
}

interface VectorResult {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  similarity_score: number;
}

interface VectorSearchResponse {
  results: VectorResult[];
  query: string;
  total_results: number;
}

export default function Home() {
  const [question, setQuestion] = useState('');
  const [llmResponse, setLlmResponse] = useState<LLMResponse | null>(null);
  const [vectorQuery, setVectorQuery] = useState('');
  const [vectorResults, setVectorResults] = useState<VectorSearchResponse | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'llm' | 'vector' | 'tts'>('llm');

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const handleLLMQuestion = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/llm/question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLlmResponse(data);
    } catch (error) {
      console.error('LLM Error:', error);
      setLlmResponse({
        answer: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        model_used: 'error',
        processing_time: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVectorSearch = async () => {
    if (!vectorQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${backendUrl}/api/vector/search?query=${encodeURIComponent(vectorQuery)}&limit=5`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setVectorResults(data);
    } catch (error) {
      console.error('Vector Search Error:', error);
      setVectorResults({
        results: [],
        query: vectorQuery,
        total_results: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTTS = async (text: string) => {
    if (!text.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setAudioUrl(audioUrl);
    } catch (error) {
      console.error('TTS Error:', error);
      alert(`TTS Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Interview System
          </h1>
          <p className="text-lg text-gray-600">
            Pillar 0: Foundational Connectivity and Static MVP
          </p>
          <div className="flex justify-center mt-4 space-x-1">
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Next.js</span>
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Express</span>
            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">FastAPI</span>
            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">LanceDB</span>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-6">
          <div className="bg-white rounded-lg p-1 shadow-sm">
            <button
              onClick={() => setActiveTab('llm')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'llm'
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              F.0.2: LLM Q&A
            </button>
            <button
              onClick={() => setActiveTab('vector')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'vector'
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              F.0.3: Vector Search
            </button>
            <button
              onClick={() => setActiveTab('tts')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'tts'
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              F.0.1: TTS Test
            </button>
          </div>
        </div>

        {/* LLM Q&A Tab */}
        {activeTab === 'llm' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">LLM Q&A Test</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ask a technical question:
                </label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="e.g., Explain REST APIs, What is database sharding?, How do microservices work?"
                />
              </div>
              <button
                onClick={handleLLMQuestion}
                disabled={loading || !question.trim()}
                className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Processing...' : 'Ask Question'}
              </button>
            </div>

            {llmResponse && (
              <div className="mt-6 p-4 bg-gray-50 rounded-md">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-medium">Answer:</h3>
                  <div className="text-xs text-gray-500">
                    {llmResponse.model_used} • {llmResponse.processing_time.toFixed(2)}s
                  </div>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{llmResponse.answer}</p>
                <button
                  onClick={() => handleTTS(llmResponse.answer)}
                  disabled={loading}
                  className="mt-3 text-sm bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 disabled:opacity-50"
                >
                  🔊 Convert to Speech
                </button>
              </div>
            )}
          </div>
        )}

        {/* Vector Search Tab */}
        {activeTab === 'vector' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Vector Search Test</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search technical documents:
                </label>
                <input
                  type="text"
                  value={vectorQuery}
                  onChange={(e) => setVectorQuery(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., sharding, REST API, microservices"
                />
              </div>
              <button
                onClick={handleVectorSearch}
                disabled={loading || !vectorQuery.trim()}
                className="bg-purple-500 text-white px-6 py-2 rounded-md hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Searching...' : 'Search Documents'}
              </button>
            </div>

            {vectorResults && (
              <div className="mt-6">
                <h3 className="font-medium mb-3">
                  Search Results ({vectorResults.total_results} found):
                </h3>
                <div className="space-y-3">
                  {vectorResults.results.map((result) => (
                    <div key={result.id} className="p-4 bg-gray-50 rounded-md">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-gray-900">{result.title}</h4>
                        <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                          {result.category}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">{result.content}</p>
                      <div className="flex justify-between items-center">
                        <div className="flex flex-wrap gap-1">
                          {result.tags.map((tag) => (
                            <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                        <span className="text-xs text-gray-500">
                          Score: {result.similarity_score.toFixed(3)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TTS Tab */}
        {activeTab === 'tts' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Text-to-Speech Test</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter text to convert to speech:
                </label>
                <textarea
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Enter any text to test TTS functionality..."
                  id="tts-input"
                />
              </div>
              <button
                onClick={() => {
                  const input = document.getElementById('tts-input') as HTMLTextAreaElement;
                  handleTTS(input.value);
                }}
                disabled={loading}
                className="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Generating...' : 'Generate Speech'}
              </button>
            </div>

            {audioUrl && (
              <div className="mt-6 p-4 bg-gray-50 rounded-md">
                <h3 className="font-medium mb-3">Generated Audio:</h3>
                <audio controls className="w-full">
                  <source src={audioUrl} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
          </div>
        )}

        {/* Checkpoints Status */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Pillar 0 Checkpoints</h2>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
              <span className="text-sm">
                <strong>Checkpoint 0.1:</strong> Verify text → TTS → audio playback works
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
              <span className="text-sm">
                <strong>Checkpoint 0.2:</strong> Test LLM responds correctly to technical questions
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
              <span className="text-sm">
                <strong>Checkpoint 0.3:</strong> Verify vector search returns expected documents
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
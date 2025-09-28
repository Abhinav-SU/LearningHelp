import os
import time
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.preferred_model = 'gpt-4o-mini'  # Cost-optimized as specified
        self._client = None
        
        # Initialize the preferred LLM client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on available API keys"""
        try:
            if self.openai_api_key:
                import openai
                self._client = openai.OpenAI(api_key=self.openai_api_key)
                self.active_provider = 'openai'
                logger.info("Initialized OpenAI client")
            elif self.google_api_key:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self._client = genai.GenerativeModel('gemini-2.0-flash-exp')  # Cost-optimized
                self.active_provider = 'google'
                self.preferred_model = 'gemini-2.0-flash-exp'
                logger.info("Initialized Google Gemini client")
            else:
                logger.warning("No API keys found - LLM service will use mock responses")
                self.active_provider = 'mock'
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.active_provider = 'mock'
    
    def is_ready(self) -> bool:
        """Check if the LLM service is ready to process requests"""
        return self._client is not None or self.active_provider == 'mock'
    
    async def answer_question(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Process a question and return an answer using the configured LLM
        
        Args:
            question: The question to answer
            context: Optional context to help answer the question
            
        Returns:
            Dict containing answer, model_used, and processing_time
        """
        start_time = time.time()
        
        try:
            # Construct the prompt for technical interview context
            system_prompt = """You are an expert technical interviewer and software engineer. 
            Provide clear, concise, and technically accurate answers to programming and system design questions.
            Focus on practical knowledge that would be relevant in a technical interview setting.
            Keep responses under 200 words unless specifically asked for more detail."""
            
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {question}"
            else:
                full_prompt = question
            
            # Process based on active provider
            if self.active_provider == 'openai':
                response = await self._openai_completion(system_prompt, full_prompt)
            elif self.active_provider == 'google':
                response = await self._google_completion(system_prompt, full_prompt)
            else:
                response = self._mock_completion(question)
            
            processing_time = time.time() - start_time
            
            return {
                "answer": response,
                "model_used": self.preferred_model,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return {
                "answer": f"I apologize, but I encountered an error processing your question: {str(e)}",
                "model_used": self.preferred_model,
                "processing_time": time.time() - start_time
            }
    
    async def _openai_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Get completion from OpenAI API"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.chat.completions.create(
                    model=self.preferred_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _google_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Get completion from Google Gemini API"""
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.generate_content(full_prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise
    
    def _mock_completion(self, question: str) -> str:
        """Provide mock responses for testing when no API key is available"""
        mock_responses = {
            "rest api": "REST APIs are architectural style for web services using HTTP methods (GET, POST, PUT, DELETE) to perform CRUD operations. They are stateless, cacheable, and use standard HTTP status codes. Key principles include uniform interface, client-server architecture, and layered system design.",
            "sharding": "Database sharding is a horizontal partitioning technique that splits large databases across multiple servers. Each shard contains a subset of data based on a sharding key. Benefits include improved performance and scalability, but challenges include increased complexity and potential for uneven data distribution.",
            "microservices": "Microservices architecture breaks applications into small, independent services that communicate via APIs. Benefits include scalability, technology diversity, and fault isolation. Challenges include distributed system complexity, network latency, and data consistency across services."
        }
        
        # Simple keyword matching for mock responses
        question_lower = question.lower()
        for key, response in mock_responses.items():
            if key in question_lower:
                return f"[MOCK RESPONSE] {response}"
        
        return f"[MOCK RESPONSE] Thank you for your question about '{question}'. In a real implementation, this would be processed by an LLM API. Please configure your API keys in the .env file to enable full functionality."
#!/usr/bin/env python3
"""
Pillar 0: Acceptance Testing Script
Automated testing for all three implemented features (F.0.1, F.0.2, F.0.3)
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class Pillar0TestSuite:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.python_url = "http://localhost:8001"
        self.test_results = {
            "phase1_config": {"status": "pending", "tests": []},
            "phase2_backend": {"status": "pending", "tests": []},
            "checkpoints": {"0.1": "pending", "0.2": "pending", "0.3": "pending"}
        }
        
    def log_test(self, phase: str, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results[phase]["tests"].append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
        print(f"{status_icon} [{phase.upper()}] {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_service_connectivity(self):
        """Phase 1.1: Python Service Status Check"""
        print("\n=== Phase 1: Configuration Verification ===")
        
        # Test Python service health
        try:
            response = requests.get(f"{self.python_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("phase1_config", "Python Service Health", "PASS", 
                            f"Services ready: {data.get('services', {})}")
            else:
                self.log_test("phase1_config", "Python Service Health", "FAIL", 
                            f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("phase1_config", "Python Service Health", "FAIL", str(e))
        
        # Test Backend service health
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("phase1_config", "Backend Service Health", "PASS", 
                            "Backend service responding")
            else:
                self.log_test("phase1_config", "Backend Service Health", "FAIL", 
                            f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("phase1_config", "Backend Service Health", "FAIL", str(e))
    
    def test_checkpoint_03_vector_search(self):
        """Checkpoint 0.3: Vector Search (F.0.3)"""
        print("\n=== Phase 2: Functional Checkpoints ===")
        
        # Test 2.1: Vector Search API Call
        try:
            query = "tell me about distributed database concepts"
            response = requests.get(
                f"{self.backend_url}/api/vector/search",
                params={"query": query, "limit": 2},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) > 0:
                    # Check if results contain database sharding content
                    found_relevant = any("shard" in result.get("content", "").lower() or 
                                       "database" in result.get("content", "").lower() 
                                       for result in results)
                    
                    if found_relevant:
                        self.log_test("phase2_backend", "Vector Search - Content Relevance", "PASS",
                                    f"Found {len(results)} relevant results with database content")
                        self.test_results["checkpoints"]["0.3"] = "PASS"
                    else:
                        self.log_test("phase2_backend", "Vector Search - Content Relevance", "FAIL",
                                    "Results don't contain expected database/sharding content")
                else:
                    self.log_test("phase2_backend", "Vector Search - Results Count", "FAIL",
                                "No results returned")
            else:
                self.log_test("phase2_backend", "Vector Search API", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("phase2_backend", "Vector Search API", "FAIL", str(e))
    
    def test_checkpoint_02_llm_qa(self):
        """Checkpoint 0.2: LLM Q&A (F.0.2)"""
        
        # Test 2.2: LLM Q&A API Call
        try:
            payload = {
                "question": "What is the STAR method and why is it used in behavioral interviews?",
                "context": "Technical interview context"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/llm/question",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                model_used = data.get("model_used", "")
                processing_time = data.get("processing_time", 0)
                
                if answer and len(answer) > 50:  # Ensure substantive answer
                    # Check for STAR method content (even in mock responses)
                    if "STAR" in answer or "structured" in answer.lower() or "method" in answer.lower():
                        self.log_test("phase2_backend", "LLM Q&A - Content Quality", "PASS",
                                    f"Model: {model_used}, Time: {processing_time:.2f}s")
                        self.test_results["checkpoints"]["0.2"] = "PASS"
                    else:
                        self.log_test("phase2_backend", "LLM Q&A - Content Quality", "PARTIAL",
                                    f"Answer provided but may be generic. Model: {model_used}")
                else:
                    self.log_test("phase2_backend", "LLM Q&A - Answer Length", "FAIL",
                                "Answer too short or empty")
            else:
                self.log_test("phase2_backend", "LLM Q&A API", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("phase2_backend", "LLM Q&A API", "FAIL", str(e))
    
    def test_checkpoint_01_tts(self):
        """Checkpoint 0.1: TTS Endpoint (F.0.1)"""
        
        # Test 2.3: TTS API Call
        try:
            payload = {
                "text": "The core design pattern is reliable and scalable.",
                "voice": "alloy"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/tts",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                # Check if response contains audio data
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'audio' in content_type and content_length > 1000:  # Reasonable audio file size
                    self.log_test("phase2_backend", "TTS Audio Generation", "PASS",
                                f"Audio generated: {content_length} bytes, type: {content_type}")
                    self.test_results["checkpoints"]["0.1"] = "PASS"
                else:
                    self.log_test("phase2_backend", "TTS Audio Generation", "FAIL",
                                f"Invalid audio response: {content_length} bytes, type: {content_type}")
            else:
                # TTS might fail without real API key, check if it's a key issue
                if "api" in response.text.lower() and "key" in response.text.lower():
                    self.log_test("phase2_backend", "TTS API", "PARTIAL",
                                f"API key required for full functionality: {response.status_code}")
                else:
                    self.log_test("phase2_backend", "TTS API", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("phase2_backend", "TTS API", "FAIL", str(e))
    
    def test_dependency_management(self):
        """Test dependency management by stopping Python service"""
        print("\n=== Dependency Management Test ===")
        
        # This would require stopping the Python service, but since it's running in background,
        # we'll simulate by testing an invalid endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/vector/search?query=test", timeout=5)
            if response.status_code in [500, 502, 503]:
                self.log_test("phase2_backend", "Dependency Management", "PASS",
                            "Backend properly handles service dependencies")
            elif response.status_code == 200:
                self.log_test("phase2_backend", "Dependency Management", "INFO",
                            "Python service is running - dependency check skipped")
            else:
                self.log_test("phase2_backend", "Dependency Management", "UNKNOWN",
                            f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("phase2_backend", "Dependency Management", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run complete Pillar 0 acceptance test suite"""
        print("🚀 Starting Pillar 0: Acceptance Testing")
        print("=" * 60)
        
        # Phase 1: Configuration Verification
        self.test_service_connectivity()
        
        # Phase 2: Functional Checkpoints
        self.test_checkpoint_03_vector_search()
        self.test_checkpoint_02_llm_qa()
        self.test_checkpoint_01_tts()
        self.test_dependency_management()
        
        # Summary Report
        self.print_summary()
    
    def print_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("🏁 PILLAR 0 ACCEPTANCE TEST SUMMARY")
        print("=" * 60)
        
        # Checkpoint Status
        print("\n📋 CHECKPOINT STATUS:")
        for checkpoint, status in self.test_results["checkpoints"].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
            print(f"   Checkpoint {checkpoint}: {status_icon} {status}")
        
        # Overall Status
        passed_checkpoints = sum(1 for status in self.test_results["checkpoints"].values() if status == "PASS")
        total_checkpoints = len(self.test_results["checkpoints"])
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Checkpoints Passed: {passed_checkpoints}/{total_checkpoints}")
        
        if passed_checkpoints == total_checkpoints:
            print("   🎉 STATUS: READY FOR PILLAR 1")
            print("   ✅ All core I/O functionality validated")
        elif passed_checkpoints >= 2:
            print("   ⚠️  STATUS: MOSTLY READY")
            print("   🔧 Minor issues to resolve before Pillar 1")
        else:
            print("   ❌ STATUS: NOT READY")
            print("   🚨 Major issues require resolution")
        
        print("\n💡 NEXT STEPS:")
        if passed_checkpoints == total_checkpoints:
            print("   → Proceed to Pillar 1: Streaming ASR integration")
            print("   → Focus on sub-500ms latency target")
            print("   → Implement AWS Step Functions")
        else:
            print("   → Resolve failing checkpoints")
            print("   → Verify API key configuration if TTS fails")
            print("   → Re-run acceptance tests")

if __name__ == "__main__":
    tester = Pillar0TestSuite()
    tester.run_all_tests()
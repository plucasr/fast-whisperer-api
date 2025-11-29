import asyncio
import io
import json
from pathlib import Path

import httpx
import pytest


class TestTranscriptionAPI:
    """Test suite for the Lexios Transcription API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def test_health_check(self):
        """Test the health check endpoint"""
        print("Testing health check...")
        response = await self.client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed\n")

    async def test_root_endpoint(self):
        """Test the root endpoint"""
        print("Testing root endpoint...")
        response = await self.client.get("/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        print("✓ Root endpoint passed\n")

    async def test_supported_languages(self):
        """Test the supported languages endpoint"""
        print("Testing supported languages...")
        response = await self.client.get("/supported-languages")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert "en" in data["languages"]
        print("✓ Supported languages passed\n")

    async def test_audio_transcription_no_file(self):
        """Test audio transcription without file (should fail)"""
        print("Testing audio transcription without file...")
        response = await self.client.post("/transcribe-audio")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 422  # Validation error
        print("✓ No file validation passed\n")

    async def test_audio_transcription_invalid_format(self):
        """Test audio transcription with invalid file format"""
        print("Testing audio transcription with invalid format...")

        # Create a fake text file
        fake_file = io.BytesIO(b"This is not an audio file")

        files = {"file": ("test.txt", fake_file, "text/plain")}
        response = await self.client.post("/transcribe-audio", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Should either return 400 or succeed with error in response
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == False
            assert "error" in data
        print("✓ Invalid format handling passed\n")

    async def test_youtube_transcript(self):
        """Test YouTube transcript functionality"""
        print("Testing YouTube transcript...")

        # Use a known video with captions
        test_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (has captions)
            "languages": ["en"],
        }

        response = await self.client.post("/transcript", json=test_data)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            if data["success"]:
                print(f"Transcript length: {data.get('length', 0)} characters")
                print(f"Sample: {data.get('transcript', '')[:100]}...")
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")

        print("✓ YouTube transcript test completed\n")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Run all tests"""
    tester = TestTranscriptionAPI()

    try:
        print("🚀 Starting API tests...\n")

        await tester.test_health_check()
        await tester.test_root_endpoint()
        await tester.test_supported_languages()
        await tester.test_audio_transcription_no_file()
        await tester.test_audio_transcription_invalid_format()
        await tester.test_youtube_transcript()

        print("✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    finally:
        await tester.close()


def run_simple_test():
    """Simple synchronous test for basic connectivity"""
    import requests

    base_url = "http://localhost:8000"

    print("🔍 Testing basic connectivity...")

    try:
        # Test health check
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Root endpoint: {response.status_code}")
        print(f"Response: {response.json()}")

        print("✅ Basic connectivity test passed!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure the API server is running on http://localhost:8000")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        run_simple_test()
    else:
        asyncio.run(main())

import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8000/chat/ws"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        # Send a message
        message = {
            "message": "Explain the concept of grace briefly.",
            "messages": []
        }
        await websocket.send(json.dumps(message))
        print(f"Sent: {message['message']}")
        
        # Listen for responses
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("status") == "streaming":
                    print(f"Chunk: {data.get('chunk')}", end="", flush=True)
                elif data.get("status") == "final":
                    print("\n[Stream Complete]")
                    break
                elif data.get("status") == "error":
                    print(f"\nError: {data.get('error')}")
                    break
            except websockets.exceptions.ConnectionClosed:
                print("\nConnection closed")
                break

if __name__ == "__main__":
    asyncio.run(test_chat())

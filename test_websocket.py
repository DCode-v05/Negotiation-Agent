#!/usr/bin/env python3
"""
Quick WebSocket test script to verify live chat functionality
"""
import asyncio
import websockets
import json
import uuid

async def test_websocket_connection():
    """Test WebSocket connection to both buyer and seller endpoints"""
    
    # Generate a test session ID
    test_session_id = str(uuid.uuid4())
    print(f"Testing with session ID: {test_session_id}")
    
    buyer_uri = f"ws://localhost:8000/ws/user/{test_session_id}"
    seller_uri = f"ws://localhost:8000/ws/seller/{test_session_id}"
    
    print("\n=== Testing Buyer WebSocket Connection ===")
    try:
        async with websockets.connect(buyer_uri) as buyer_ws:
            print("✅ Buyer WebSocket connected successfully")
            
            # Listen for connection confirmation
            response = await buyer_ws.recv()
            data = json.loads(response)
            print(f"Buyer received: {data}")
            
            print("\n=== Testing Seller WebSocket Connection ===")
            try:
                async with websockets.connect(seller_uri) as seller_ws:
                    print("✅ Seller WebSocket connected successfully")
                    
                    # Listen for connection confirmation
                    response = await seller_ws.recv()
                    data = json.loads(response)
                    print(f"Seller received: {data}")
                    
                    print("\n=== Testing Message Exchange ===")
                    
                    # Send a test message from seller
                    test_message = {
                        "type": "message",
                        "content": "Hello, this is a test message from seller!",
                        "session_id": test_session_id
                    }
                    
                    await seller_ws.send(json.dumps(test_message))
                    print("📤 Seller sent test message")
                    
                    # Wait for any responses
                    try:
                        # Check if buyer receives the seller message
                        buyer_response = await asyncio.wait_for(buyer_ws.recv(), timeout=5.0)
                        buyer_data = json.loads(buyer_response)
                        print(f"📥 Buyer received: {buyer_data}")
                        
                        # Check if seller receives AI response
                        seller_response = await asyncio.wait_for(seller_ws.recv(), timeout=10.0)
                        seller_data = json.loads(seller_response)
                        print(f"📥 Seller received AI response: {seller_data}")
                        
                        print("\n✅ Live chat test successful!")
                        
                    except asyncio.TimeoutError:
                        print("⚠️  Timeout waiting for message responses")
                        
            except Exception as e:
                print(f"❌ Seller WebSocket error: {e}")
                
    except Exception as e:
        print(f"❌ Buyer WebSocket error: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Live Chat Functionality")
    print("=" * 50)
    asyncio.run(test_websocket_connection())
import asyncio
import json
import websockets

async def simulate():
    uri = "ws://localhost:8085/ws/cockpit"
    async with websockets.connect(uri) as websocket:
        print("Connected. Sending test Ignition Strike for AVAXUSDT...")
        payload = {
            "type": "ignition_strike",
            "data": {
                "symbol": "AVAXUSDT",
                "side": "BUY",
                "score": 95,
                "strategy": "MOLA_EXTREME"
            }
        }
        await websocket.send(json.dumps(payload))
        print("Strike sent! Check the Observatory.")

if __name__ == "__main__":
    asyncio.run(simulate())

import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.agents.ai_service import ai_service

async def test():
    status = ai_service.get_cascade_status()
    print("AI Cascade Status:")
    for m in status['cascade']:
        print(f"- {m['model']}: {m['status']}")
    
    print(f"\nLast model: {status['last_model']}")

if __name__ == "__main__":
    asyncio.run(test())

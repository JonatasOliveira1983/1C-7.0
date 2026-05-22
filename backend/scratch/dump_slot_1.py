import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

async def main():
    try:
        from services.sovereign_service import sovereign_service
        slot = await sovereign_service.get_slot(1)
        print(f"SLOT 1 FULL DATA: {json.dumps(slot, indent=2)}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())

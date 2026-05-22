import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())
from services.database_service import database_service

async def main():
    await database_service.initialize()
    trades = await database_service.get_trade_history(limit=5, symbol="OPUSDT")
    res = []
    for t in trades:
        # Convert datetime objects to string
        t_dict = dict(t)
        if 'timestamp' in t_dict and t_dict['timestamp']:
            t_dict['timestamp'] = t_dict['timestamp'].isoformat()
        res.append(t_dict)
    
    with open('op_trades_dump.json', 'w') as f:
        json.dump(res, f, indent=2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        pass

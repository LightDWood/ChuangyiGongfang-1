import asyncio
import sys
sys.path.insert(0, 'backend')

from app.agents.lead_agent import LeadAgent
from app.database import init_db, get_db

async def test_lead_agent():
    await init_db()
    db_gen = get_db()
    db = await db_gen.__anext__()

    agent = LeadAgent(db)

    print("测试 LeadAgent.process_user_input")
    print("=" * 60)

    try:
        count = 0
        async for chunk in agent.process_user_input('做一个资讯监测工具', 'test-session', 'test-user'):
            print(f"Event {count}: type={chunk.get('type')}, content={chunk.get('content', '')[:50]}...")
            count += 1
            if count > 20:
                print("Too many events, stopping...")
                break
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_lead_agent())

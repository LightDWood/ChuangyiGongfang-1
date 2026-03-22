import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        login_data = {"username": "testuser_e2e", "password": "testpass123"}
        login_resp = await client.post(
            "http://localhost:8000/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_resp.json().get("access_token")
        print(f"Token: {token[:20]}...")

        session_resp = await client.post(
            "http://localhost:8000/api/sessions",
            json={"title": "Test Stream"},
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = session_resp.json().get("id")
        print(f"Session: {session_id}")

        print("\nTesting SSE stream...")
        async with client.stream(
            "GET",
            f"http://localhost:8000/api/sessions/{session_id}/stream",
            params={"content": "做一个资讯监测工具", "token": token}
        ) as resp:
            print(f"Status: {resp.status_code}")
            event_count = 0
            async for line in resp.aiter_lines():
                if line.startswith("event:") or line.startswith("data:"):
                    print(line[:100])
                    event_count += 1
                if event_count > 15:
                    break
            print(f"\nTotal events received: {event_count}")

asyncio.run(test())

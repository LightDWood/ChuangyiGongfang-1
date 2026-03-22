import json
import urllib.request
import urllib.parse

def make_request(method, url, data=None, headers=None):
    if headers is None:
        headers = {}

    if data is not None:
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode()
        elif isinstance(data, str):
            data = data.encode()

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def main():
    base_url = "http://localhost:8000/api"

    print("=" * 60)
    print("测试会话服务")
    print("=" * 60)

    # 登录
    status, body = make_request(
        "POST",
        f"{base_url}/auth/login",
        data={"username": "testuser_e2e", "password": "testpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"1. 登录: status={status}")
    if status != 200:
        print(f"   失败: {body}")
        return
    token = json.loads(body).get("access_token")
    print(f"   成功, token={token[:20]}...")

    # 创建会话
    status, body = make_request(
        "POST",
        f"{base_url}/sessions",
        data=json.dumps({"title": "测试会话"}),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    print(f"2. 创建会话: status={status}")
    if status != 200:
        print(f"   失败: {body}")
        return
    session_id = json.loads(body).get("id")
    print(f"   成功, session_id={session_id}")

    # 测试非流式消息接口
    print(f"3. 测试 POST /messages (非流式):")
    status, body = make_request(
        "POST",
        f"{base_url}/sessions/{session_id}/messages",
        data=json.dumps({"content": "做一个资讯监测工具"}),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    print(f"   status={status}")
    if status == 200:
        result = json.loads(body)
        print(f"   content: {result.get('content', '')[:200]}...")
    else:
        print(f"   失败: {body}")

if __name__ == "__main__":
    main()

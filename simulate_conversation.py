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
        with urllib.request.urlopen(req, timeout=180) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def stream_sse(url, params):
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            for line in response:
                decoded = line.decode('utf-8').strip()
                yield decoded
    except Exception as e:
        yield f"error: {e}"

def main():
    base_url = "http://localhost:8000/api"

    print("=" * 60)
    print("开始模拟用户需求对话")
    print("=" * 60)

    status, body = make_request(
        "POST",
        f"{base_url}/auth/login",
        data={"username": "testuser_e2e", "password": "testpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if status != 200:
        print(f"登录失败: {body}")
        return
    token = json.loads(body).get("access_token")
    print(f"✓ 登录成功\n")

    status, body = make_request(
        "POST",
        f"{base_url}/sessions",
        data=json.dumps({"title": "模拟需求对话"}),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    session_id = json.loads(body).get("id")
    print(f"✓ 会话创建成功: {session_id}\n")

    conversation_rounds = [
        ("做一个资讯监测工具", "第1轮 - 用户初次提出需求"),
        ("需要监控科技、创业、风险投资相关的新闻", "第2轮 - 用户补充目标领域"),
        ("主要是微信公众号和微博的内容", "第3轮 - 用户指定内容来源"),
        ("每天早上9点推送，给我就行不需要分享功能", "第4轮 - 用户明确推送时间和功能偏好"),
        ("简洁实用就好，不需要太复杂", "第5轮 - 用户明确产品定位")
    ]

    for i, (user_input, description) in enumerate(conversation_rounds, 1):
        print("-" * 60)
        print(f"【{description}】")
        print(f"用户: {user_input}")
        print("AI: ", end="", flush=True)

        event_count = 0
        last_content = ""

        for line in stream_sse(
            f"{base_url}/sessions/{session_id}/stream",
            {"content": user_input, "token": token}
        ):
            if line.startswith("event:"):
                event_type = line.replace("event:", "").strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line.replace("data:", "").strip())
                    content = data.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        last_content = content
                        event_count += 1
                except json.JSONDecodeError:
                    pass
            elif line == "":
                if event_count > 0:
                    break

        print("\n")
        print(f"  [收到 {event_count} 个内容片段]")
        print()

    print("=" * 60)
    print("对话模拟完成")
    print("=" * 60)

    status, body = make_request(
        "GET",
        f"{base_url}/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    messages = json.loads(body)
    print(f"\n会话共 {len(messages)} 条消息")
    for msg in messages:
        role = "用户" if msg["role"] == "user" else "AI"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"  [{role}] {content}")

if __name__ == "__main__":
    main()

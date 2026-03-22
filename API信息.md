API Key:
apikey-69b8f5c1e4b0c281b94a4c49
模型列表及测试样例

 curl --location 'https://modelapi-test.haier.net/model/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Qwen3.5-35B-A3B",
    "stream": true,
    "max_tokens": 1024,
    "top_p": 0.95,
    "temperature": 1,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "你是谁？"
        }
    ]
}'

curl --location 'https://modelapi-test.haier.net/model/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "MiniMax-M2",
    "stream": true,
    "max_tokens": 1024,
    "top_p": 0.95,
    "temperature": 1,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "你是谁？"
        }
    ]
}'

curl --location 'https://modelapi-test.haier.net/model/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "deepseek-v3",
    "stream": true,
    "max_tokens": 1024,
    "top_p": 0.95,
    "temperature": 1,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "你是谁？"
        }
    ]
}'

curl --location 'https://modelapi-test.haier.net/model/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Qwen3-Coder-480B-A35B-Instruct",
    "stream": true,
    "max_tokens": 1024,
    "top_p": 0.95,
    "temperature": 1,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "你是谁？"
        }
    ]
}'
"""手动脚本：启动后端后执行 `python scripts/test_chat_api.py`，勿依赖 pytest 收集。"""

import json

import requests

url = "http://localhost:8000/api/v1/ai/chat"
test_data = {
    "message": "你好，请介绍一下你自己",
    "history": [],
}


def main() -> None:
    print("🧪 测试 AI 对话接口...")
    print(f"URL: {url}")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False)}\n")

    try:
        response = requests.post(url, json=test_data, timeout=60)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print("\n响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✅ 测试成功！AI 对话接口正常工作")
        else:
            print(f"\n❌ 测试失败！状态码: {response.status_code}")

    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")


if __name__ == "__main__":
    main()

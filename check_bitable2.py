#!/usr/bin/env python3
import json
import requests
from feishu_config import get_app_id, get_app_secret

app_id = get_app_id()
app_secret = get_app_secret()

# 获取token
resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", json={
    "app_id": app_id,
    "app_secret": app_secret
})
token = resp.json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 获取表列表
app_token = "VBqEbUOEhaFmjOsnHjqcEcOanId"
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
resp = requests.get(url, headers=headers)
data = resp.json()
print("表列表:")
print(json.dumps(data, indent=2, ensure_ascii=False))

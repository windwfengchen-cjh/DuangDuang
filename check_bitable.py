#!/usr/bin/env python3
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

# 获取表字段
app_token = "VBqEbUOEhaFmjOsnHjqcEcOanId"
table_id = "tblRc2E1VOWxFGte"

url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
resp = requests.get(url, headers=headers)
data = resp.json()
print("表字段列表:")
for field in data.get("data", {}).get("items", []):
    print(f"  - {field.get('field_name')} (type: {field.get('field_type')})")

#!/usr/bin/env python3
"""
删除需求跟进清单表中的所有记录
"""
import json
import os
import requests

REQUIREMENT_APP_TOKEN = "Op8WbbFewaq1tasfO8IcQkXmnFf"
REQUIREMENT_TABLE_ID = "tbl0vJo8gPHIeZ9y"

def load_feishu_creds():
    """从配置文件加载飞书凭证"""
    try:
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data}")
    return data.get('tenant_access_token')

def list_all_records(app_token, table_id, token):
    """列出表中所有记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 500}
    
    records = []
    page_token = None
    
    while True:
        if page_token:
            params["page_token"] = page_token
        
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"❌ 获取记录失败: {data}")
            break
        
        items = data.get('data', {}).get('items', [])
        records.extend(items)
        
        if not data.get('data', {}).get('has_more'):
            break
        page_token = data.get('data', {}).get('page_token')
    
    return records

def delete_record(app_token, table_id, record_id, token):
    """删除单条记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.delete(url, headers=headers)
    data = resp.json()
    
    if data.get('code') == 0:
        print(f"✅ 已删除记录: {record_id}")
        return True
    else:
        print(f"❌ 删除失败 {record_id}: {data}")
        return False

def main():
    print("=" * 60)
    print("🗑️ 删除需求跟进清单表中的所有记录")
    print("=" * 60)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法加载飞书凭证")
        return
    
    # 获取 token
    try:
        token = get_tenant_access_token(app_id, app_secret)
        print(f"✅ 获取 token 成功")
    except Exception as e:
        print(f"❌ 获取 token 失败: {e}")
        return
    
    # 获取所有记录
    print("\n📋 获取记录列表...")
    records = list_all_records(REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID, token)
    print(f"找到 {len(records)} 条记录")
    
    if not records:
        print("⚠️ 表中没有记录，无需删除")
        return
    
    # 显示记录
    print("\n记录列表:")
    for i, record in enumerate(records, 1):
        fields = record.get('fields', {})
        name = fields.get('需求跟进清单', '未知')
        status = fields.get('需求状态', '未知')
        print(f"  {i}. {name} [{status}] (ID: {record['record_id']})")
    
    # 删除所有记录
    print(f"\n🗑️ 开始删除 {len(records)} 条记录...")
    success_count = 0
    fail_count = 0
    
    for record in records:
        record_id = record['record_id']
        if delete_record(REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID, record_id, token):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("📊 删除结果")
    print("=" * 60)
    print(f"✅ 成功: {success_count} 条")
    print(f"❌ 失败: {fail_count} 条")
    
    if fail_count > 0:
        print("\n⚠️ 部分记录删除失败，可能是权限问题")

if __name__ == "__main__":
    main()

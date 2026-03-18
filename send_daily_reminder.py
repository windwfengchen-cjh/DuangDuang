#!/usr/bin/env python3
"""发送每日汇总提醒到个人"""
import json
import os
import sys

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

def load_feishu_creds():
    """从 OpenClaw 配置加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"Failed to get token: {result}")
        return result.get('tenant_access_token')

def send_text_message(user_id, text):
    """发送文本消息到个人"""
    import urllib.request
    import ssl
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        raise Exception("Feishu credentials not found")
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 使用 open_id 发送个人消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    
    payload = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False)
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result

def main():
    from datetime import datetime
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = "ou_3e48baef1bd71cc89fb5a364be55cafc"
    
    msg = f"""📊 今日问题汇总提醒 ({today})

请查看业务反馈问题记录表了解今日收集的问题：
https://gz-junbo.feishu.cn/base/KNiibDP6KaRwopsPbRucr752ntg

💡 如需自动汇总，请联系生成详细报告~"""
    
    try:
        result = send_text_message(user_id, msg)
        if result.get('code') == 0:
            print(f"[{datetime.now()}] 汇总提醒发送成功")
        else:
            print(f"[{datetime.now()}] 发送失败: {result.get('msg')}")
            sys.exit(1)
    except Exception as e:
        print(f"[{datetime.now()}] 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

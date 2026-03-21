#!/usr/bin/env python3
"""
飞书私聊问题解决工具
用于测试和解决私聊发送问题
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CONTACTS_FILE = "/home/admin/openclaw/workspace/feishu_contacts.json"

def load_feishu_creds() -> Tuple[Optional[str], Optional[str]]:
    """从 OpenClaw 配置加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"获取token失败: {result}")
        return result.get('tenant_access_token')

def send_p2p_message(token: str, user_id: str, message: str) -> Dict:
    """
    发送私聊消息
    
    Returns:
        Dict: 包含code、msg、success等字段的结果
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    data = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": message})
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {
                'success': True,
                'code': result.get('code'),
                'message_id': result.get('data', {}).get('message_id'),
                'raw': result
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            return {
                'success': False,
                'code': error_data.get('code'),
                'msg': error_data.get('msg'),
                'log_id': error_data.get('error', {}).get('log_id'),
                'raw': error_data
            }
        except:
            return {
                'success': False,
                'code': e.code,
                'msg': error_body,
                'raw': error_body
            }

def load_contacts() -> Dict:
    """加载联系人映射表"""
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def check_user_p2p_availability(token: str, user_id: str, contacts: Dict = None) -> Dict:
    """
    检查用户是否可以接收私聊消息
    
    Returns:
        Dict: 检查结果和状态
    """
    if contacts is None:
        contacts = load_contacts()
    
    user_name = contacts.get(user_id, {}).get('name', 'Unknown')
    
    # 尝试发送测试消息
    result = send_p2p_message(token, user_id, "【系统测试】这是一条连接测试消息")
    
    if result.get('success'):
        return {
            'available': True,
            'user_id': user_id,
            'user_name': user_name,
            'message': '✅ 用户已建立私聊会话，可以正常发送消息',
            'solution': None
        }
    
    error_code = result.get('code')
    error_msg = result.get('msg', '')
    
    # 分析错误类型
    if error_code == 230013 or 'NO availability' in error_msg or 'invisible' in error_msg:
        return {
            'available': False,
            'user_id': user_id,
            'user_name': user_name,
            'error_code': error_code,
            'error_msg': error_msg,
            'message': f'❌ 用户不在机器人可用性范围内',
            'solution': 'availability',
            'details': {
                'problem': '机器人应用未被配置为对该用户可见',
                'fix_methods': [
                    '方法1: 让管理员在飞书后台将该用户加入应用可用性范围',
                    '方法2: 让用户在飞书客户端中主动搜索机器人并发送任意消息',
                    '方法3: 将用户和机器人加入同一群聊，并在群内互动'
                ]
            }
        }
    elif error_code == 41050 or 'no user authority' in error_msg:
        return {
            'available': False,
            'user_id': user_id,
            'user_name': user_name,
            'error_code': error_code,
            'error_msg': error_msg,
            'message': f'❌ 应用缺少查询用户信息的权限',
            'solution': 'permission',
            'details': {
                'problem': '应用缺少 contact:user.base:readonly 权限',
                'fix_methods': [
                    '在飞书开发者后台申请 contact:user.base:readonly 权限',
                    '但这不影响发送消息，只是无法获取用户详情'
                ]
            }
        }
    else:
        return {
            'available': False,
            'user_id': user_id,
            'user_name': user_name,
            'error_code': error_code,
            'error_msg': error_msg,
            'message': f'❌ 未知错误',
            'solution': 'unknown',
            'details': {
                'problem': f'错误码: {error_code}, 消息: {error_msg}',
                'fix_methods': ['查看飞书开放平台文档或联系技术支持']
            }
        }

def test_all_contacts():
    """测试所有联系人的私聊可用性"""
    print("="*70)
    print("飞书私聊可用性检查工具")
    print("="*70)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法加载飞书凭证")
        return
    
    print(f"✅ 凭证加载成功\n")
    
    # 获取token
    token = get_tenant_access_token(app_id, app_secret)
    
    # 加载联系人
    contacts = load_contacts()
    
    print(f"共有 {len(contacts)} 位联系人需要检查\n")
    print("-"*70)
    
    available_count = 0
    unavailable_count = 0
    
    for user_id, info in contacts.items():
        result = check_user_p2p_availability(token, user_id, contacts)
        user_name = info.get('name', 'Unknown')
        
        if result.get('available'):
            available_count += 1
            print(f"✅ {user_name} ({user_id[:20]}...)")
        else:
            unavailable_count += 1
            print(f"❌ {user_name} ({user_id[:20]}...)")
            print(f"   错误: {result.get('error_msg', 'Unknown')}")
            if result.get('solution') == 'availability':
                print(f"   解决: 需要将用户加入应用可用性范围")
        
        print()
    
    print("-"*70)
    print(f"\n检查结果汇总:")
    print(f"  ✅ 可用: {available_count} 人")
    print(f"  ❌ 不可用: {unavailable_count} 人")
    print(f"  📊 总计: {len(contacts)} 人")
    
    if unavailable_count > 0:
        print(f"\n⚠️ 注意: 有 {unavailable_count} 位用户无法接收私聊消息")
        print(f"   解决方案: 参考 SOLUTION_REPORT.md")

def test_single_user(user_id: str):
    """测试单个用户的私聊可用性"""
    print("="*70)
    print("飞书私聊可用性检查 - 单个用户")
    print("="*70)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法加载飞书凭证")
        return
    
    token = get_tenant_access_token(app_id, app_secret)
    contacts = load_contacts()
    
    user_name = contacts.get(user_id, {}).get('name', 'Unknown')
    print(f"\n检查用户: {user_name}")
    print(f"Open ID: {user_id}")
    print(f"来源: {contacts.get(user_id, {}).get('source', 'Unknown')}")
    print("-"*70)
    
    result = check_user_p2p_availability(token, user_id, contacts)
    
    print(f"\n结果: {result.get('message')}")
    
    if not result.get('available') and result.get('details'):
        print(f"\n问题分析:")
        print(f"  {result['details'].get('problem')}")
        print(f"\n解决方法:")
        for i, method in enumerate(result['details'].get('fix_methods', []), 1):
            print(f"  {i}. {method}")
    
    return result.get('available')

def generate_solution_report():
    """生成解决方案报告"""
    report = '''# 飞书私聊问题解决方案

## 问题诊断

### 根本原因
根据API测试，私聊发送失败的根本原因是：

**错误码 230013**: "Bot has NO availability to this user."
**错误码 232043**: "bot is invisible to user ids"

这意味着机器人应用未被配置为对目标用户"可见"。飞书的权限模型要求：
1. 用户必须在应用的"可用性范围"内
2. 或用户必须主动与机器人建立过会话关系

## 解决方案

### 方案一：管理员配置可用性范围（推荐）

**操作步骤：**
1. 组织管理员登录 [飞书管理后台](https://feishu.cn/admin)
2. 进入 **工作台** → **应用管理**
3. 找到当前应用（OpenClaw机器人）
4. 点击 **可用性设置**
5. 添加需要接收私聊的用户或部门：
   - 添加单个用户：搜索并选择"梁思洁"
   - 或添加整个部门：选择"产研-融合业务组"
6. 保存设置

**优点：**
- 一劳永逸，配置后所有目标用户都能接收消息
- 无需用户主动操作

**缺点：**
- 需要组织管理员权限
- 可能需要重新发布应用版本

---

### 方案二：引导用户主动建立会话

**操作步骤：**
1. 在"产研-融合业务组"群（oc_469678cc3cd264438f9bbb65da534c0b）发送消息：
   ```
   📢 系统通知
   
   如需接收个人消息提醒，请按以下步骤操作：
   1. 在飞书搜索框搜索 "OpenClaw"
   2. 点击机器人头像进入私聊
   3. 发送任意消息（如"你好"）
   4. 完成！此后您将能接收个人通知
   ```

2. 或者发送一个带回调按钮的卡片消息

**优点：**
- 无需管理员权限
- 立即可用

**缺点：**
- 需要用户主动操作
- 无法保证所有用户都会执行

---

### 方案三：通过群聊@提醒替代私聊

**替代方案：**
如果无法解决私聊问题，可以在群内@用户：

```python
# 在原群内@用户提醒
send_group_message(
    chat_id="oc_469678cc3cd264438f9bbb65da534c0b",
    content=f"@{user_name} 您有一条新消息...",
    at_list=[user_id]
)
```

**优点：**
- 无需额外配置
- 公开透明，便于跟踪

**缺点：**
- 隐私性较差
- 群内其他成员也能看到

---

## 快速行动建议

### 针对梁思洁（ou_d03303783b5538c608b540dc8ad9ac87）

**立即行动：**
1. 在"产研-融合业务组"群中@梁思洁，告知其需要私聊机器人建立会话
2. 或联系组织管理员将"产研-融合业务组"加入应用可用性范围

**验证方法：**
运行以下命令测试：
```bash
python3 feishu_p2p_solution.py test ou_d03303783b5538c608b540dc8ad9ac87
```

---

## 技术细节

### 当前已拥有的权限
- ✅ `im:message:send_as_bot` - 机器人发送消息基础权限
- ✅ `im:message.group_msg` - 群聊消息发送
- ✅ `im:chat:read` - 读取会话信息
- ✅ `im:message.p2p_msg:readonly` - 读取私聊消息

### 缺失的权限（非必需）
- ❌ `im:message.p2p_msg` - 发送单聊消息（注意：即使有此权限，仍需可用性范围配置）

### 关键发现
1. **飞书没有API可以直接创建1对1会话** - 会话只能通过用户主动行为建立
2. **权限和可用性是两回事** - 有权限不代表可以给任意用户发消息
3. **可用性范围控制最严格** - 这是最底层的访问控制

---

## 参考文档

- [配置应用可用性](https://open.feishu.cn/document/home/introduction-to-scope-and-authorization/availability)
- [发送消息API](https://open.feishu.cn/document/server-docs/im-v1/message/create)
- [飞书权限列表](https://open.feishu.cn/document/server-docs/permission-list)

---

*报告生成时间: 2026-03-21*
'''
    
    report_file = "/home/admin/openclaw/workspace/SOLUTION_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 解决方案报告已保存到: {report_file}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            if len(sys.argv) > 2:
                user_id = sys.argv[2]
                test_single_user(user_id)
            else:
                print("用法: python3 feishu_p2p_solution.py test <user_id>")
        elif command == 'check':
            test_all_contacts()
        elif command == 'report':
            generate_solution_report()
        else:
            print(f"未知命令: {command}")
            print("用法:")
            print("  python3 feishu_p2p_solution.py test <user_id>  # 测试单个用户")
            print("  python3 feishu_p2p_solution.py check            # 检查所有联系人")
            print("  python3 feishu_p2p_solution.py report           # 生成解决方案报告")
    else:
        # 默认生成报告并检查所有
        generate_solution_report()
        print()
        test_all_contacts()

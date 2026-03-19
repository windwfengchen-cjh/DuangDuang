#!/usr/bin/env python3
"""发送每日问题反馈详细报告"""
import json
import os
import sys
from datetime import datetime, timedelta
import urllib.request
import ssl

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
BITABLE_APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
BITABLE_TABLE_ID = "tblyDHrGGTQTaex6"

# 报告接收人 (Boss)
REPORT_USER_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"

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

def get_today_records():
    """获取今日的所有记录"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return []
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 获取今天的日期范围（毫秒时间戳）
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
    today_end = today_start + timedelta(days=1)
    
    start_ts = int(today_start.timestamp() * 1000)
    end_ts = int(today_end.timestamp() * 1000)
    
    all_records = []
    page_token = None
    
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"
        
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('code') != 0:
                    print(f"API 错误: {result}")
                    break
                
                data = result.get('data', {})
                records = data.get('items', [])
                
                # 过滤今日记录
                for record in records:
                    fields = record.get('fields', {})
                    feedback_time = fields.get('反馈时间', '')
                    
                    # 解析反馈时间
                    if isinstance(feedback_time, int):
                        record_ts = feedback_time
                        if start_ts <= record_ts < end_ts:
                            all_records.append(record)
                    elif isinstance(feedback_time, str):
                        # 尝试解析字符串日期
                        try:
                            dt = datetime.strptime(feedback_time[:10], '%Y/%m/%d')
                            record_ts = int(dt.timestamp() * 1000)
                            if start_ts <= record_ts < end_ts:
                                all_records.append(record)
                        except:
                            # 如果无法解析，根据记录ID或创建时间判断
                            pass
                
                page_token = data.get('page_token')
                if not page_token or not data.get('has_more'):
                    break
        except Exception as e:
            print(f"获取记录失败: {e}")
            break
    
    return all_records

def analyze_records(records):
    """分析记录数据"""
    stats = {
        'total': len(records),
        'by_type': {'问题': 0, '需求': 0, '未知': 0},
        'by_status': {'待处理': 0, '处理中': 0, '已解决': 0, '已关闭': 0, '其他': 0},
        'by_source': {},
        'pending': [],  # 待跟进事项
        'resolved_today': [],  # 今日已解决
    }
    
    for record in records:
        fields = record.get('fields', {})
        
        # 类型统计
        record_type = fields.get('类型', '未知')
        if record_type in stats['by_type']:
            stats['by_type'][record_type] += 1
        else:
            stats['by_type']['未知'] += 1
        
        # 状态统计
        status = fields.get('处理状态', '其他')
        if status in stats['by_status']:
            stats['by_status'][status] += 1
        else:
            stats['by_status']['其他'] += 1
        
        # 来源统计
        source = fields.get('来源群', fields.get('反馈来源', '未知'))
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        # 待跟进事项（待处理或处理中）
        if status in ['待处理', '处理中']:
            stats['pending'].append({
                'title': fields.get('业务反馈问题记录表', '无标题'),
                'type': record_type,
                'status': status,
                'source': source,
                'feedback_by': fields.get('反馈人', '未知'),
                'handler': fields.get('处理人', []),
                'content': fields.get('问题内容', '')[:100] + '...' if len(fields.get('问题内容', '')) > 100 else fields.get('问题内容', '')
            })
        
        # 今日已解决
        if status == '已解决':
            stats['resolved_today'].append({
                'title': fields.get('业务反馈问题记录表', '无标题'),
                'type': record_type,
                'source': source,
                'feedback_by': fields.get('反馈人', '未知'),
                'result': fields.get('处理结果', ''),
            })
    
    return stats

def get_handler_names(handler_list):
    """获取处理人姓名列表"""
    if not handler_list:
        return '未分配'
    
    # 处理人映射
    handler_map = {
        'ou_82e152d737ab5aedee7110066828b5a1': '施嘉科',
        'ou_cbcd1090961b620a4500ce68e3c81952': '宋广智',
        'ou_3e48baef1bd71cc89fb5a364be55cafc': '陈俊洪',
    }
    
    names = []
    for h in handler_list:
        if isinstance(h, dict):
            uid = h.get('id', '')
            name = h.get('name', '') or handler_map.get(uid, uid[:8] if uid else '未知')
            names.append(name)
        elif isinstance(h, str):
            names.append(handler_map.get(h, h[:8]))
    
    return '、'.join(names) if names else '未分配'

def generate_report(stats, today_str):
    """生成详细报告"""
    lines = []
    
    # 报告标题
    lines.append(f"📊 每日问题反馈报告 ({today_str})")
    lines.append("=" * 50)
    lines.append("")
    
    # 一、总览统计
    lines.append("📈 【总览统计】")
    lines.append(f"  • 今日总记录数：{stats['total']} 条")
    lines.append(f"  • 问题反馈：{stats['by_type'].get('问题', 0)} 条")
    lines.append(f"  • 需求建议：{stats['by_type'].get('需求', 0)} 条")
    lines.append("")
    
    # 二、处理状态分布
    lines.append("📋 【处理状态分布】")
    for status, count in stats['by_status'].items():
        if count > 0:
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            lines.append(f"  • {status}：{count} 条 ({percentage:.1f}%)")
    lines.append("")
    
    # 三、按来源群分组
    lines.append("🏢 【按来源群分布】")
    if stats['by_source']:
        for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {source}：{count} 条")
    else:
        lines.append("  • 无数据来源记录")
    lines.append("")
    
    # 四、待跟进事项
    lines.append("⚠️ 【待跟进事项】")
    pending_count = len(stats['pending'])
    if pending_count > 0:
        lines.append(f"共 {pending_count} 项需要关注：")
        lines.append("")
        for i, item in enumerate(stats['pending'], 1):
            lines.append(f"  {i}. 【{item['type']}】{item['title']}")
            lines.append(f"     状态：{item['status']} | 来源：{item['source']}")
            lines.append(f"     反馈人：{item['feedback_by']} | 处理人：{get_handler_names(item['handler'])}")
            if item['content']:
                lines.append(f"     内容：{item['content']}")
            lines.append("")
    else:
        lines.append("  ✅ 今日无待跟进事项")
    lines.append("")
    
    # 五、今日已解决
    resolved_count = len(stats['resolved_today'])
    if resolved_count > 0:
        lines.append("✅ 【今日已解决】")
        lines.append(f"共 {resolved_count} 项已处理完成：")
        lines.append("")
        for i, item in enumerate(stats['resolved_today'], 1):
            lines.append(f"  {i}. 【{item['type']}】{item['title']}")
            lines.append(f"     来源：{item['source']} | 反馈人：{item['feedback_by']}")
            if item['result']:
                lines.append(f"     处理结果：{item['result'][:80]}..." if len(item['result']) > 80 else f"     处理结果：{item['result']}")
            lines.append("")
        lines.append("")
    
    # 六、关键洞察
    lines.append("💡 【关键洞察】")
    
    # 洞察1：处理效率
    pending_ratio = (stats['by_status'].get('待处理', 0) / stats['total'] * 100) if stats['total'] > 0 else 0
    if pending_ratio > 50:
        lines.append(f"  ⚠️ 待处理比例较高（{pending_ratio:.1f}%），建议加快处理进度")
    elif stats['by_status'].get('已解决', 0) > 0:
        lines.append(f"  ✅ 今日处理效率良好，已解决 {stats['by_status'].get('已解决', 0)} 个问题")
    
    # 洞察2：类型分布
    if stats['by_type'].get('需求', 0) > stats['by_type'].get('问题', 0):
        lines.append(f"  📌 今日以需求建议为主（{stats['by_type'].get('需求', 0)} 条），建议安排需求评审")
    elif stats['by_type'].get('问题', 0) > 0:
        lines.append(f"  🔧 今日问题反馈 {stats['by_type'].get('问题', 0)} 条，请关注稳定性")
    
    # 洞察3：来源集中
    if stats['by_source']:
        max_source = max(stats['by_source'].items(), key=lambda x: x[1])
        if max_source[1] > stats['total'] * 0.6:
            lines.append(f"  🎯 反馈主要来自【{max_source[0]}】（{max_source[1]} 条），建议重点关注")
    
    # 如果没有任何数据
    if stats['total'] == 0:
        lines.append("  📭 今日暂无新增反馈记录")
    
    lines.append("")
    lines.append("-" * 50)
    lines.append("📎 查看完整表格：https://gz-junbo.feishu.cn/base/KNiibDP6KaRwopsPbRucr752ntg")
    
    return "\n".join(lines)

def send_report(user_id, report_text):
    """发送报告消息到个人"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        raise Exception("Feishu credentials not found")
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    
    payload = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": report_text}, ensure_ascii=False)
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
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"[{datetime.now()}] 开始生成每日报告...")
    
    # 获取今日记录
    print(f"[{datetime.now()}] 正在查询今日记录...")
    records = get_today_records()
    print(f"[{datetime.now()}] 获取到 {len(records)} 条今日记录")
    
    # 分析数据
    print(f"[{datetime.now()}] 正在分析数据...")
    stats = analyze_records(records)
    
    # 生成报告
    print(f"[{datetime.now()}] 正在生成报告...")
    report = generate_report(stats, today)
    
    # 发送报告
    print(f"[{datetime.now()}] 正在发送报告...")
    try:
        result = send_report(REPORT_USER_ID, report)
        if result.get('code') == 0:
            print(f"[{datetime.now()}] 报告发送成功")
        else:
            print(f"[{datetime.now()}] 发送失败: {result.get('msg')}")
            sys.exit(1)
    except Exception as e:
        print(f"[{datetime.now()}] 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

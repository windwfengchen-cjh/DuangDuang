#!/usr/bin/env python3
"""
上线自检脚本
重新上线后执行，检查离线期间遗漏的@消息
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace')

from event_cache import check_missed_messages, generate_offline_report
from datetime import datetime

def main():
    print("=" * 60)
    print("🔄 OpenClaw 上线自检")
    print(f"时间: {datetime.now()}")
    print("=" * 60)
    
    # 检查事件缓存中的未处理消息
    print("\n📋 检查事件缓存...")
    unprocessed = check_missed_messages()
    
    if unprocessed:
        print("\n" + "=" * 60)
        print("⚠️ 发现未处理的@消息，需要补录！")
        print("=" * 60)
        
        report = generate_offline_report()
        print(report)
        
        print("\n请Boss确认：")
        print("1. 上述消息是否已通过引用方式补录？")
        print("2. 如有遗漏，请在群内引用原消息并@我跟进")
        
        return 1  # 有未处理消息
    else:
        print("\n✅ 事件缓存正常，无遗漏")
        return 0  # 正常

if __name__ == '__main__':
    exit(main())

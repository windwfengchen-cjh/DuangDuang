#!/usr/bin/env python3
"""
⚠️ DEPRECATED: This Python script is deprecated as of requirement-follow v2.0.0

The research chat monitoring logic has been migrated to TypeScript and is now
fully implemented in ../src/index.ts

Please use the TypeScript implementation instead:
- Import from: requirement-follow/src/index.ts
- Main handler: RequirementFollowHandler class
- Core functions: handleResearchMessage, createResearchSession, startResearch

This file is kept for reference only and will be removed in a future version.
"""

# DEPRECATED: Requirement Research Chat Monitor (Python version)
# Migration date: 2025-03-24
# Migrated to: requirement-follow/src/index.ts

import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path


# NEW: Research Questions for QA Mode
RESEARCH_QUESTIONS = [
    {
        "key": "background",
        "question": "**问题 1/7：业务背景**\n\n请描述一下这个需求的【业务背景】是什么？是在什么场景下产生的？\n\n💡 提示：为什么需要这个功能？要解决什么业务问题？"
    },
    {
        "key": "target_users",
        "question": "**问题 2/7：目标用户**\n\n这个需求的【目标用户】是谁？\n\n💡 例如：内部同事（哪个部门/角色？）、外部客户、特定群体等"
    },
    {
        "key": "current_situation",
        "question": "**问题 3/7：现状描述**\n\n请描述一下【当前的系统/流程现状】是什么样？\n\n💡 提示：用户现在是如何完成这个任务的？"
    },
    {
        "key": "pain_points",
        "question": "**问题 4/7：核心痛点**\n\n当前的【核心痛点】是什么？\n\n💡 提示：哪个步骤最耗时/容易出错？造成了什么影响？"
    },
    {
        "key": "expected_solution",
        "question": "**问题 5/7：期望解决方案**\n\n针对这个痛点，您【期望的解决方案】是什么？\n\n💡 提示：希望系统如何帮助用户？"
    },
    {
        "key": "priority",
        "question": "**问题 6/7：优先级和时间**\n\n请问这个需求的【优先级和时间要求】是怎样的？\n\n💡 例如：高/中/低，期望上线时间"
    },
    {
        "key": "attachments",
        "question": "**问题 7/7：相关资料**\n\n是否有相关的【数据、截图、文档】需要补充？如有请直接发送，没有请回复\"无\"。"
    }
]


@dataclass
class ChatMessage:
    """Represents a chat message"""
    sender: str
    sender_name: str
    content: str
    time: str
    message_id: str


@dataclass
class ChatContext:
    """Maintains chat context and history"""
    messages: List[ChatMessage]
    requirement_info: Dict[str, Any]
    start_time: str
    last_activity: str
    requirement_id: str
    # NEW: QA Mode fields
    qa_mode: bool = False
    current_question_idx: int = 0
    collected_answers: Dict[str, str] = field(default_factory=dict)
    questions_sent: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'messages': [asdict(m) for m in self.messages],
            'requirement_info': self.requirement_info,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'requirement_id': self.requirement_id,
            'qa_mode': self.qa_mode,
            'current_question_idx': self.current_question_idx,
            'collected_answers': self.collected_answers,
            'questions_sent': self.questions_sent
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatContext':
        messages = [ChatMessage(**m) for m in data.get('messages', [])]
        return cls(
            messages=messages,
            requirement_info=data.get('requirement_info', {}),
            start_time=data.get('start_time', datetime.now().isoformat()),
            last_activity=data.get('last_activity', datetime.now().isoformat()),
            requirement_id=data.get('requirement_id', ''),
            qa_mode=data.get('qa_mode', False),
            current_question_idx=data.get('current_question_idx', 0),
            collected_answers=data.get('collected_answers', {}),
            questions_sent=data.get('questions_sent', [])
        )


class ContextManager:
    """Manages chat context persistence"""
    
    def __init__(self, requirement_id: str, context_dir: str = '/tmp/requirement_follow'):
        self.requirement_id = requirement_id
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.context_file = self.context_dir / f'{requirement_id}.json'
    
    def save(self, context: ChatContext) -> None:
        """Save context to file"""
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load(self) -> Optional[ChatContext]:
        """Load context from file"""
        if self.context_file.exists():
            with open(self.context_file, 'r', encoding='utf-8') as f:
                return ChatContext.from_dict(json.load(f))
        return None
    
    def append_message(self, message: ChatMessage) -> ChatContext:
        """Append message to context and save"""
        context = self.load() or ChatContext(
            messages=[],
            requirement_info={},
            start_time=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            requirement_id=self.requirement_id
        )
        
        context.messages.append(message)
        context.last_activity = datetime.now().isoformat()
        
        # Keep only last 100 messages
        if len(context.messages) > 100:
            context.messages = context.messages[-100:]
        
        self.save(context)
        return context


class TriggerDetector:
    """Detects trigger words and commands in messages"""
    
    TRIGGER_WORDS = ['生成prd', '完成调研', 'generate_prd', 'prd', '完成']
    
    @classmethod
    def is_trigger(cls, content: str) -> bool:
        """Check if content contains trigger words"""
        content_lower = content.lower()
        return any(word in content_lower for word in cls.TRIGGER_WORDS)
    
    @classmethod
    def parse_command(cls, content: str) -> Optional[Dict[str, str]]:
        """Parse command from content"""
        content_lower = content.lower()
        
        if any(kw in content_lower for kw in ['生成.*prd', 'prd.*生成', '完成.*调研', 'generate.*prd']):
            return {'type': 'prd', 'action': 'generate'}
        if any(kw in content_lower for kw in ['状态', 'status', '进度']):
            return {'type': 'status', 'action': 'check'}
        if any(kw in content_lower for kw in ['结束', '完成', '退出', 'stop', 'end']):
            return {'type': 'control', 'action': 'exit'}
        
        return None


class ChatMonitor:
    """Monitors chat for requirement follow skill"""
    
    def __init__(self, chat_id: str, requirement_id: str, requester_id: str,
                 app_token: str = '', table_id: str = ''):
        self.chat_id = chat_id
        self.requirement_id = requirement_id
        self.requester_id = requester_id
        self.app_token = app_token
        self.table_id = table_id
        self.context_manager = ContextManager(requirement_id)
        self.processed_ids = set()
        self.is_running = True
    
    def send_message(self, content: str) -> bool:
        """Send message to chat"""
        try:
            # Use message tool
            import subprocess
            result = subprocess.run([
                'python3', '-c',
                f'from tools import message; message.send(target="{self.chat_id}", message="""{content}""")'
            ], capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    def poll_messages(self) -> List[Dict]:
        """Poll new messages from chat"""
        # This would integrate with actual message API
        # For now, return empty list (handled by TypeScript main handler)
        return []
    
    # NEW: QA Mode methods
    def send_next_question(self, context: ChatContext) -> bool:
        """Send next question in QA mode"""
        if not context.qa_mode:
            return False
        
        if context.current_question_idx >= len(RESEARCH_QUESTIONS):
            return False
        
        # Avoid sending duplicate questions
        if context.current_question_idx in context.questions_sent:
            return True
        
        question = RESEARCH_QUESTIONS[context.current_question_idx]
        print(f"📤 Sending question {context.current_question_idx + 1}/{len(RESEARCH_QUESTIONS)}: {question['key']}")
        
        success = self.send_message(question['question'])
        if success:
            context.questions_sent.append(context.current_question_idx)
            self.context_manager.save(context)
        return success
    
    def advance_to_next_question(self, context: ChatContext, answer: str) -> bool:
        """Save answer and advance to next question"""
        if not context.qa_mode:
            return False
        
        # Save answer
        current_question = RESEARCH_QUESTIONS[context.current_question_idx]
        context.collected_answers[current_question['key']] = answer
        print(f"💾 Saved answer for {current_question['key']}: {answer[:50]}...")
        
        # Move to next question
        context.current_question_idx += 1
        self.context_manager.save(context)
        
        # Check if all questions answered
        if context.current_question_idx >= len(RESEARCH_QUESTIONS):
            print("✅ All questions answered!")
            self.send_message("✅ 所有问题已回答完毕！正在准备生成 PRD...")
            time.sleep(2)
            return self.generate_prd()
        else:
            # Send next question
            return self.send_next_question(context)
    
    def is_from_requirement_person(self, sender_id: str) -> bool:
        """Check if message is from requirement person"""
        return sender_id == self.requester_id
    
    def generate_prd(self) -> bool:
        """Generate PRD document"""
        print("📝 Generating PRD...")
        
        # Load context
        context = self.context_manager.load()
        if not context:
            print("❌ No context found")
            return False
        
        # NEW: Include QA data if available
        qa_data = None
        if context.qa_mode:
            qa_data = {
                'answers': context.collected_answers,
                'question_count': context.current_question_idx
            }
        
        # Prepare data for PRD generation
        context_data = {
            'requirement_id': self.requirement_id,
            'chat_context': [asdict(m) for m in context.messages],
            'qa_data': qa_data,
            'start_time': context.start_time,
            'message_count': len(context.messages),
            'requirement_info': context.requirement_info
        }
        
        try:
            # Call requirement_follow.py complete function
            result = subprocess.run([
                'python3', '/home/admin/openclaw/workspace/requirement_follow.py',
                'complete', self.requirement_id,
                '--context', json.dumps(context_data)
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ PRD generated successfully")
                
                # NEW: Include QA summary if in QA mode
                completion_message = (
                    f"✅ PRD 文档已生成完成！\n\n"
                    f"需求 ID: {self.requirement_id}\n"
                    f"消息记录: {len(context.messages)} 条"
                )
                
                if context.qa_mode:
                    completion_message += f"\n问题回答: {context.current_question_idx}/7"
                
                completion_message += "\n\n调研流程已完成。"
                
                self.send_message(completion_message)
                return True
            else:
                print(f"❌ PRD generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating PRD: {e}")
            return False
    
    def get_status(self) -> str:
        """Get current monitoring status"""
        context = self.context_manager.load()
        if not context:
            return "📊 暂无状态信息"
        
        start = datetime.fromisoformat(context.start_time)
        duration = datetime.now() - start
        minutes = int(duration.total_seconds() / 60)
        
        # NEW: Show QA progress if in QA mode
        qa_info = ""
        if context.qa_mode:
            qa_info = f"• 问答进度: {context.current_question_idx}/7\n"
        
        return (
            f"📊 当前状态:\n"
            f"• 需求ID: {self.requirement_id}\n"
            f"• 运行时长: {minutes} 分钟\n"
            f"• 消息记录: {len(context.messages)} 条\n"
            f"{qa_info}"
            f"• 最后活动: {context.last_activity}\n\n"
            f"发送\"生成PRD\"或\"完成调研\"来结束调研并生成文档。"
        )
    
    def handle_message(self, message: Dict) -> bool:
        """Handle incoming message, returns True if should exit"""
        msg_id = message.get('message_id')
        if msg_id in self.processed_ids:
            return False
        self.processed_ids.add(msg_id)
        
        content = message.get('content', '')
        sender = message.get('sender', {})
        
        print(f"[{datetime.now().isoformat()}] {sender.get('name', 'Unknown')}: {content[:50]}...")
        
        # Save to context
        chat_msg = ChatMessage(
            sender=sender.get('id', ''),
            sender_name=sender.get('name', 'Unknown'),
            content=content,
            time=message.get('create_time', datetime.now().isoformat()),
            message_id=msg_id
        )
        self.context_manager.append_message(chat_msg)
        
        # NEW: QA Mode - Check if message is from requirement person and advance question
        context = self.context_manager.load()
        if context and context.qa_mode:
            sender_id = sender.get('id', '')
            if self.is_from_requirement_person(sender_id):
                # Skip if this is a question we sent (avoid detecting own messages)
                is_bot_message = any(q['question'][:20] in content for q in RESEARCH_QUESTIONS)
                if not is_bot_message and context.current_question_idx < len(RESEARCH_QUESTIONS):
                    self.advance_to_next_question(context, content)
        
        # Check for commands
        command = TriggerDetector.parse_command(content)
        if command:
            if command['type'] == 'prd':
                if self.generate_prd():
                    return True  # Signal to exit
            elif command['type'] == 'status':
                self.send_message(self.get_status())
            elif command['type'] == 'control':
                self.send_message("👋 助手即将退出，感谢使用！")
                return True
        
        return False
    
    def run(self, timeout_hours: int = 24, qa_mode: bool = False, 
            requester_name: str = '需求人') -> None:
        """Run the monitor loop"""
        print(f"🚀 Starting chat monitor for requirement {self.requirement_id}")
        print(f"   Chat ID: {self.chat_id}")
        print(f"   QA Mode: {qa_mode}")
        print(f"   Timeout: {timeout_hours} hours")
        
        # Initialize QA mode in context
        context = self.context_manager.load()
        if not context:
            context = ChatContext(
                messages=[],
                requirement_info={},
                start_time=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
                requirement_id=self.requirement_id,
                qa_mode=qa_mode
            )
            self.context_manager.save(context)
        else:
            context.qa_mode = qa_mode
            self.context_manager.save(context)
        
        # NEW: Send appropriate startup message based on mode
        if qa_mode:
            welcome_msg = (
                f"👋 大家好！需求调研现在开始。\n\n"
                f"📋 **需求标题**: 待补充\n"
                f"👤 **需求人**: @{requester_name}\n\n"
                f"🤖 我将通过 **7个关键问题** 引导调研，同时 **自动收集** 群内所有讨论内容。\n\n"
                f"请 @{requester_name} 准备回答第一个问题..."
            )
            self.send_message(welcome_msg)
            
            # NEW: Send first question after delay
            time.sleep(3)
            self.send_next_question(context)
        else:
            self.send_message(
                "🤖 需求调研助手已启动\n\n"
                "我会自动收集群里的需求信息，当需要生成PRD时，请发送\"生成PRD\"或\"完成调研\"。"
            )
        
        # Set timeout
        timeout_at = datetime.now() + timedelta(hours=timeout_hours)
        
        try:
            while self.is_running and datetime.now() < timeout_at:
                # Poll messages (actual implementation would integrate with message API)
                messages = self.poll_messages()
                
                for msg in messages:
                    should_exit = self.handle_message(msg)
                    if should_exit:
                        print("✅ Task completed, exiting...")
                        return
                
                time.sleep(3)  # Poll every 3 seconds
            
            # Timeout reached
            if datetime.now() >= timeout_at:
                print("⏰ Timeout reached")
                self.send_message("⏰ 调研时间已超时，助手将退出。如需继续请重新启动。")
                
        except KeyboardInterrupt:
            print("\n👋 Graceful shutdown...")
            self.send_message("👋 助手已退出")


def main():
    parser = argparse.ArgumentParser(description='Requirement Research Chat Monitor')
    parser.add_argument('--chat-id', required=True, help='Chat group ID')
    parser.add_argument('--requirement-id', required=True, help='Requirement record ID')
    parser.add_argument('--requester-id', required=True, help='Requester ID')
    parser.add_argument('--requester-name', default='需求人', help='Requester name for @mention')
    parser.add_argument('--app-token', default='', help='Bitable app token')
    parser.add_argument('--table-id', default='', help='Bitable table ID')
    parser.add_argument('--timeout', type=int, default=24, help='Timeout in hours')
    parser.add_argument('--qa-mode', action='store_true', help='Enable QA + Auto-Collect Hybrid Mode')
    parser.add_argument('--mode', choices=['monitor', 'generate'], default='monitor',
                        help='Operation mode')
    
    args = parser.parse_args()
    
    if args.mode == 'monitor':
        monitor = ChatMonitor(
            chat_id=args.chat_id,
            requirement_id=args.requirement_id,
            requester_id=args.requester_id,
            app_token=args.app_token,
            table_id=args.table_id
        )
        monitor.run(
            timeout_hours=args.timeout,
            qa_mode=args.qa_mode,
            requester_name=args.requester_name
        )
    elif args.mode == 'generate':
        # Direct PRD generation mode
        monitor = ChatMonitor(
            chat_id=args.chat_id,
            requirement_id=args.requirement_id,
            requester_id=args.requester_id
        )
        monitor.generate_prd()


if __name__ == '__main__':
    main()

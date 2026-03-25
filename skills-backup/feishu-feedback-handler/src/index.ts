/**
 * 飞书反馈处理 Skill - 简化版 v3.1
 * 需求跟进逻辑直接调用 requirement-follow skill
 */

import * as path from 'path';
import { loadConfig, ForwardConfig } from './config';
import { Forwarder, ForwardResult, MessageType } from './forwarder';
import { BitableClient } from './bitable';
import { getTenantAccessToken, removeAtTags, sendFeishuMessage } from './utils';

// 直接导入 requirement-follow skill 的核心类
import { RequirementFollowWorkflow, getDefaultConfig as getRFConfig } from 'requirement-follow';

const REQUIREMENT_FOLLOW_TRIGGERS = ['跟进这个需求', '跟进需求', '记录这个需求', '跟进一下这个需求', '记录一下这个需求'];
const BOT_ID = 'ou_428d1d5b99e0bb6d1c26549c70688cfb';

function isRequirementFollowCommand(text: string): boolean {
  return REQUIREMENT_FOLLOW_TRIGGERS.some(t => text.toLowerCase().includes(t));
}

function extractTextFromContent(content: any): string {
  if (content.text) return content.text;
  if (content.post?.zh_cn) {
    let text = content.post.zh_cn.title || '';
    for (const block of content.post.zh_cn.content || []) {
      for (const item of block) {
        if (item.tag === 'text') text += item.text;
        if (item.tag === 'at') text += `@${item.user_name}`;
      }
    }
    return text.trim();
  }
  return '';
}

/**
 * 获取被引用的消息内容
 */
async function fetchQuotedMessage(messageId: string, token: string): Promise<{ content: string; sender: { sender_id: { open_id: string }; sender_name?: string } } | null> {
  try {
    const response = await fetch(`https://open.feishu.cn/open-apis/im/v1/messages/${messageId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      console.error(`  ❌ 获取被引用消息失败: ${response.status}`);
      return null;
    }

    const data = await response.json();
    if (data.code !== 0 || !data.data) {
      console.error(`  ❌ 获取被引用消息API错误: ${data.msg || 'unknown'}`);
      return null;
    }

    const message = data.data;
    return {
      content: message.content || '',
      sender: {
        sender_id: { open_id: message.sender?.sender_id?.open_id || '' },
        sender_name: message.sender?.sender_name
      }
    };
  } catch (error) {
    console.error('  ❌ 获取被引用消息异常:', error);
    return null;
  }
}

function classifyMessage(text: string): MessageType {
  const lower = text.toLowerCase();
  const demandKeywords = ['需求', '建议', '优化', '改进', '建议增加', '希望有', '能否'];
  const consultKeywords = ['如何使用', '怎么操作', '在哪里', '咨询', '问一下'];
  if (demandKeywords.some(k => lower.includes(k))) return '需求';
  if (consultKeywords.some(k => lower.includes(k))) return '咨询';
  return '问题';
}

export interface FeishuMessageEvent {
  message_id: string;
  chat_id: string;
  chat_type: 'group' | 'p2p';
  sender: { sender_id: { open_id: string }; sender_type: string; sender_name?: string; sender_email?: string };
  message_type: string;
  content: string;
  mentions?: Array<{ key: string; id: { open_id: string }; name: string; tenant_key: string }>;
  create_time: string;
  update_time: string;
  root_id?: string;  // 被引用消息的ID
  parent_id?: string; // 父消息ID
}

export class FeedbackHandler {
  private config: any;
  private forwarder: Forwarder;
  private bitable: BitableClient;
  private token: string | null = null;
  private tokenExpiry: number = 0;

  constructor() {
    this.config = loadConfig();
    this.forwarder = new Forwarder(this.config);
    this.bitable = new BitableClient(this.config.bitable);
  }

  private async getToken(): Promise<string> {
    const now = Date.now();
    if (this.token && now < this.tokenExpiry) return this.token;
    this.token = await getTenantAccessToken();
    this.tokenExpiry = now + 1.5 * 60 * 60 * 1000;
    this.forwarder.setToken(this.token);
    this.bitable.setToken(this.token);
    return this.token;
  }

  private isAtMe(event: FeishuMessageEvent): boolean {
    return event.mentions?.some(m => m.id.open_id === BOT_ID) ?? false;
  }

  async handleMessage(event: FeishuMessageEvent): Promise<any> {
    console.log(`[${new Date().toISOString()}] 收到消息 from ${event.sender.sender_name || 'Unknown'}`);
    if (!this.isAtMe(event)) return { handled: false, reason: 'not_at_me' };

    const forwardConfig = this.config.forwardConfigs[event.chat_id];

    let textContent = '';
    try { textContent = extractTextFromContent(JSON.parse(event.content)); } catch { textContent = event.content; }
    const cleanText = removeAtTags(textContent);
    console.log(`  内容: ${cleanText.substring(0, 50)}...`);

    await this.getToken();

    // 需求跟进指令在任何群都可用
    if (isRequirementFollowCommand(cleanText)) {
      return this.handleRequirementFollow(event, cleanText, forwardConfig || {
        target_chat_id: '',
        handlers: [],
        source_name: '未知来源群',
        record_bitable: true,
        notify_boss_for_requirement: true
      });
    }

    // 其他功能（转发、跟进等）仍需配置
    if (!forwardConfig) return { handled: false, reason: 'config_not_found' };

    if (this.isFollowUpCommand(cleanText)) return this.handleFollowUp(event, cleanText, forwardConfig);
    
    const messageType = classifyMessage(cleanText);
    if (messageType === '咨询') return this.handleConsultation(event, cleanText, forwardConfig);
    return this.handleFeedback(event, cleanText, messageType as MessageType, forwardConfig);
  }

  private isFollowUpCommand(text: string): boolean {
    if (isRequirementFollowCommand(text)) return false;
    return ['跟进', '跟一下', '追踪', '查一下', '处理一下'].some(k => text.includes(k));
  }



  /**
   * 处理需求跟进指令 - 直接调用 requirement-follow workflow
   */
  private async handleRequirementFollow(event: FeishuMessageEvent, text: string, config: ForwardConfig): Promise<any> {
    console.log('  🚀 处理需求跟进指令');
    
    // 检查是否有被引用的消息
    let quotedContent = '';
    let requesterName = event.sender.sender_name || 'Unknown';
    let requesterId = event.sender.sender_id.open_id;
    
    if (event.root_id) {
      console.log(`  📎 检测到引用消息，root_id: ${event.root_id}`);
      const quotedMessage = await fetchQuotedMessage(event.root_id, this.token!);
      if (quotedMessage) {
        quotedContent = quotedMessage.content;
        requesterName = quotedMessage.sender.sender_name || requesterName;
        requesterId = quotedMessage.sender.sender_id.open_id || requesterId;
        console.log(`  ✅ 获取到被引用消息，发送者: ${requesterName}`);
      } else {
        console.log('  ⚠️ 无法获取被引用消息，使用当前消息');
      }
    }

    // 提取需求标题（优先使用被引用消息的内容）
    let requirementTitle = '新需求';
    const contentToParse = quotedContent || event.content;
    try {
      const content = JSON.parse(contentToParse);
      if (content.post?.zh_cn?.title) requirementTitle = content.post.zh_cn.title;
      else requirementTitle = removeAtTags(content.text || '').split('\n')[0].slice(0, 30) || '新需求';
    } catch {
      requirementTitle = text.split('\n')[0].slice(0, 30) || '新需求';
    }

    // 直接调用 requirement-follow workflow
    try {
      const rfConfig = getRFConfig();
      if (!rfConfig) {
        throw new Error('无法加载 requirement-follow 配置');
      }

      const workflow = new RequirementFollowWorkflow(rfConfig);
      const result = await workflow.startWorkflow({
        requirementContent: requirementTitle,
        requesterName: requesterName,
        requesterId: requesterId,
        sourceChatId: event.chat_id,
        sourceChatName: config.source_name,
        originalMessageId: event.root_id || event.message_id
      });

      if (result.success) {
        console.log('  ✅ 需求跟进流程启动成功');
        
        if (result.isDuplicate) {
          await sendFeishuMessage(
            event.chat_id,
            `⚠️ 发现相似需求 (记录ID: ${result.existingRecordId})，无需重复创建。`,
            this.token!
          );
        } else {
          await sendFeishuMessage(
            event.chat_id,
            `✅ 需求已记录并启动跟进流程\n\n📋 需求: ${requirementTitle}\n🆔 记录ID: ${result.recordId}\n💬 调研群: ${result.chatName}`,
            this.token!
          );
        }

        return {
          handled: true,
          type: 'requirement_follow',
          success: true,
          recordId: result.recordId,
          chatId: result.chatId,
          chatName: result.chatName,
          isDuplicate: result.isDuplicate,
          sourceChatId: event.chat_id,
          sourceChatName: config.source_name,
          requesterName: requesterName,
          requesterId: requesterId,
          requirementContent: requirementTitle
        };
      } else {
        throw new Error(result.error || '启动需求跟进流程失败');
      }
    } catch (error) {
      console.error('  ❌ 启动 requirement-follow 失败:', error);
      await sendFeishuMessage(
        event.chat_id,
        `⚠️ 需求处理失败: ${error}`,
        this.token!
      );
      return { handled: true, type: 'requirement_follow', success: false, error: String(error) };
    }
  }



  private async handleFollowUp(event: FeishuMessageEvent, text: string, config: ForwardConfig): Promise<any> {
    return this.handleFeedback(event, text, '问题', config);
  }

  private async handleConsultation(event: FeishuMessageEvent, text: string, config: ForwardConfig): Promise<any> {
    const result = await this.forwarder.forwardMessage({
      sourceChat: config.source_name, reporter: event.sender.sender_name || 'Unknown',
      content: text, messageType: '咨询', sourceChatId: event.chat_id,
      messageId: event.message_id, recordBitable: false
    });
    return { handled: true, type: 'consultation', forwarded: result.success, result };
  }

  private async handleFeedback(event: FeishuMessageEvent, text: string, messageType: MessageType, config: ForwardConfig): Promise<any> {
    const result = await this.forwarder.forwardMessage({
      sourceChat: config.source_name, reporter: event.sender.sender_name || 'Unknown',
      content: text, messageType, sourceChatId: event.chat_id,
      messageId: event.message_id, recordBitable: config.record_bitable
    });
    if (!result.success) return { handled: true, type: 'feedback', forwarded: false, error: result.error };

    let recordId: string | null = null;
    if (config.record_bitable) {
      try {
        recordId = await this.bitable.createRecord({
          title: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
          feedbackTime: Date.now(),
          feedbackUser: event.sender.sender_name || 'Unknown',
          feedbackSource: config.source_name, content: text,
          sourceChatId: event.chat_id, type: messageType as '问题' | '需求',
          originalMessageId: event.message_id
        });
      } catch (e) { console.error('记录失败:', e); }
    }
    return { handled: true, type: 'feedback', forwarded: true, recordId, result };
  }

  private extractKeywords(text: string): string[] {
    const keywords = ['同步', '数据', '订单', '导入', 'CSV', '派卡', '公众号', '通知', '抢单', '交付', '系统', '接口', '历史订单', '重新同步', '统计', '配置', '关闭', '登录', '报错', '故障', '异常', 'bug', '问题'];
    return keywords.filter(k => text.includes(k));
  }

  async handleStatusUpdate(event: FeishuMessageEvent): Promise<any> {
    if (!this.isAtMe(event)) return { handled: false, reason: 'not_at_me' };
    
    let textContent = '';
    try { textContent = extractTextFromContent(JSON.parse(event.content)); } catch { textContent = event.content; }
    const cleanText = removeAtTags(textContent);
    const senderName = event.sender.sender_name || '处理人';

    await this.getToken();

    const { status, result } = this.extractStatusAndResult(cleanText);
    const keywords = this.extractKeywords(cleanText);
    if (keywords.length === 0) return { handled: false, reason: 'no_keywords' };

    const matchedRecord = await this.bitable.findRecordByKeywords(keywords);
    if (!matchedRecord) return { handled: false, reason: 'no_matched_record' };

    const updated = await this.bitable.updateRecordStatus(matchedRecord.record_id, status || '已解决', result);
    if (updated) {
      const forwarded = await this.forwarder.forwardReplyToSource({ matchedRecord, status: status || '已解决', result, senderName });
      return { handled: true, type: 'status_update', updated: true, forwarded, recordId: matchedRecord.record_id };
    }
    return { handled: true, type: 'status_update', updated: false };
  }

  private extractStatusAndResult(text: string): { status: string | null; result: string } {
    const statusKeywords: Record<string, string[]> = {
      '已解决': ['已解决', '已完成', '搞定', '已修复', 'ok', 'OK', '已处理', '解决了', '完成了', '已上线'],
      '已关闭': ['已关闭', '无需处理', '重复问题'],
      '处理中': ['处理中', '正在处理', '跟进中'],
      '待处理': ['待处理']
    };
    for (const [status, keywords] of Object.entries(statusKeywords)) {
      for (const kw of keywords) {
        if (text.includes(kw)) {
          for (const sent of text.split(/[。！？\n]/)) {
            if (sent.includes(kw)) return { status, result: sent.trim() };
          }
          return { status, result: text.substring(0, 100) };
        }
      }
    }
    return { status: null, result: text.substring(0, 100) };
  }
}

export default FeedbackHandler;

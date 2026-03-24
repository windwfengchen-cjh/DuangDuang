/**
 * 飞书反馈处理 Skill - 主入口
 * 接收飞书事件，调用转发/更新功能
 */

import * as path from 'path';
import { loadConfig, ForwardConfig } from './config';
import { Forwarder, ForwardResult, MessageType } from './forwarder';
import { BitableClient } from './bitable';
import { getTenantAccessToken, removeAtTags } from './utils';

/**
 * 需求跟进触发词
 */
const REQUIREMENT_FOLLOW_TRIGGERS = [
  '跟进这个需求',
  '跟进需求',
  '记录这个需求',
  '跟进一下这个需求',
  '记录一下这个需求'
];

/**
 * 判断是否是需求跟进指令
 */
function isRequirementFollowCommand(text: string): boolean {
  const lowerText = text.toLowerCase();
  return REQUIREMENT_FOLLOW_TRIGGERS.some(trigger => lowerText.includes(trigger));
}

/**
 * 判断消息类型
 */
function classifyMessage(text: string): MessageType {
  const lowerText = text.toLowerCase();

  // 需求关键词
  const demandKeywords = ['需求', '建议', '优化', '改进', '建议增加', '希望有', '能否', '能不能'];
  if (demandKeywords.some(kw => lowerText.includes(kw))) {
    return '需求';
  }

  // 咨询关键词
  const consultKeywords = ['如何使用', '怎么操作', '在哪里', '咨询', '问一下'];
  if (consultKeywords.some(kw => lowerText.includes(kw))) {
    return '咨询';
  }

  // 默认识别为问题
  return '问题';
}

// 机器人ID
const BOT_ID = 'ou_428d1d5b99e0bb6d1c26549c70688cfb';

/**
 * 处理飞书消息事件
 */
export interface FeishuMessageEvent {
  message_id: string;
  chat_id: string;
  chat_type: 'group' | 'p2p';
  sender: {
    sender_id: {
      open_id: string;
    };
    sender_type: string;
    sender_name?: string;
    sender_email?: string;
  };
  message_type: 'text' | 'post' | 'image' | 'file' | 'audio' | 'media' | 'sticker';
  content: string;
  mentions?: Array<{
    key: string;
    id: {
      open_id: string;
    };
    name: string;
    tenant_key: string;
  }>;
  create_time: string;
  update_time: string;
}

/**
 * 主处理器类
 */
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

  /**
   * 获取有效的 tenant_access_token
   */
  private async getToken(): Promise<string> {
    const now = Date.now();
    if (this.token && now < this.tokenExpiry) {
      return this.token;
    }

    this.token = await getTenantAccessToken();
    // Token 有效期约2小时，这里设置1.5小时过期
    this.tokenExpiry = now + 1.5 * 60 * 60 * 1000;
    
    // 更新 forwarder 和 bitable 的 token
    this.forwarder.setToken(this.token);
    this.bitable.setToken(this.token);
    
    return this.token;
  }

  /**
   * 检查消息是否@了机器人
   */
  private isAtMe(event: FeishuMessageEvent): boolean {
    if (!event.mentions || event.mentions.length === 0) {
      return false;
    }
    return event.mentions.some(m => m.id.open_id === BOT_ID);
  }

  /**
   * 处理消息事件
   */
  async handleMessage(event: FeishuMessageEvent): Promise<any> {
    console.log(`[${new Date().toISOString()}] 收到消息 from ${event.sender.sender_name || 'Unknown'}`);
    
    // 检查是否@我
    if (!this.isAtMe(event)) {
      console.log('  未@我，忽略');
      return { handled: false, reason: 'not_at_me' };
    }

    const sourceChatId = event.chat_id;
    const forwardConfig = this.config.forwardConfigs[sourceChatId];
    if (!forwardConfig) {
      console.error(`  ❌ 未找到来源群配置: ${sourceChatId}`);
      return { handled: false, reason: 'config_not_found', error: `未找到来源群配置: ${sourceChatId}` };
    }

    // 获取纯文本内容
    let textContent = '';
    try {
      const content = JSON.parse(event.content);
      textContent = content.text || '';
    } catch {
      textContent = event.content;
    }

    // 移除@标签
    const cleanText = removeAtTags(textContent);
    console.log(`  内容: ${cleanText.substring(0, 50)}...`);

    await this.getToken();

    // 优先检查是否是需求跟进指令（必须在 isFollowUpCommand 之前检查）
    if (isRequirementFollowCommand(cleanText)) {
      console.log('  类型: 需求跟进指令');
      return this.handleRequirementFollow(event, cleanText, forwardConfig);
    }

    // 判断是否是问题跟进指令
    if (this.isFollowUpCommand(cleanText)) {
      return this.handleFollowUp(event, cleanText, forwardConfig);
    }

    // 判断消息类型
    const messageType = classifyMessage(cleanText);
    
    // 功能咨询类 - 只转发不记录表格
    if (messageType === '咨询') {
      console.log('  类型: 功能咨询（仅转发，不记录表格）');
      return this.handleConsultation(event, cleanText, forwardConfig);
    }

    // 问题/需求类 - 完整流程
    console.log(`  类型: ${messageType}`);
    return this.handleFeedback(event, cleanText, messageType as MessageType, forwardConfig);
  }

  /**
   * 判断是否是跟进指令（排除需求跟进）
   */
  private isFollowUpCommand(text: string): boolean {
    // 如果已经是需求跟进指令，不要作为问题跟进处理
    if (isRequirementFollowCommand(text)) {
      return false;
    }
    const followUpKeywords = ['跟进', '跟一下', '追踪', '查一下', '处理一下'];
    return followUpKeywords.some(kw => text.includes(kw));
  }

  /**
   * 处理需求跟进指令
   */
  private async handleRequirementFollow(
    event: FeishuMessageEvent,
    text: string,
    config: ForwardConfig
  ): Promise<any> {
    console.log('  🚀 处理需求跟进指令');

    const sender = event.sender;
    const senderName = sender.sender_name || 'Unknown';
    const senderId = sender.sender_id.open_id;
    const chatId = event.chat_id;
    const messageId = event.message_id;
    const createTime = event.create_time;

    try {
      // 调用 requirement_follow.py 启动需求跟进流程
      const { spawn } = require('child_process');
      const path = require('path');

      const eventData = {
        sender: {
          sender_name: senderName,
          sender_id: { open_id: senderId }
        },
        content: text,
        chat_id: chatId,
        message_id: messageId,
        create_time: createTime
      };

      return new Promise((resolve, reject) => {
        const pythonScript = path.join('/home/admin/openclaw/workspace', 'requirement_follow.py');
        const pythonProcess = spawn('python3', [pythonScript], {
          cwd: '/home/admin/openclaw/workspace'
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data: Buffer) => {
          stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data: Buffer) => {
          stderr += data.toString();
        });

        pythonProcess.on('close', (code: number) => {
          if (code !== 0) {
            console.error(`  ❌ 需求跟进脚本执行失败: ${stderr}`);
            resolve({
              handled: true,
              type: 'requirement_follow',
              success: false,
              error: stderr || '脚本执行失败'
            });
          } else {
            console.log(`  ✅ 需求跟进流程已启动`);
            console.log(`  📤 输出: ${stdout.substring(0, 200)}...`);
            resolve({
              handled: true,
              type: 'requirement_follow',
              success: true,
              output: stdout
            });
          }
        });

        // 发送事件数据到 Python 脚本
        pythonProcess.stdin.write(JSON.stringify(eventData));
        pythonProcess.stdin.end();
      });
    } catch (error) {
      console.error(`  ❌ 需求跟进处理异常: ${error}`);
      return {
        handled: true,
        type: 'requirement_follow',
        success: false,
        error: String(error)
      };
    }
  }

  /**
   * 处理跟进指令
   */
  private async handleFollowUp(
    event: FeishuMessageEvent,
    text: string,
    config: ForwardConfig
  ): Promise<any> {
    console.log('  处理跟进指令');
    
    // 提取问题关键词
    const keywords = this.extractKeywords(text);
    
    // 查询表格是否已有记录
    const existingRecord = await this.bitable.findRecordByKeywords(keywords);
    
    if (existingRecord) {
      console.log(`  找到已有记录: ${existingRecord.fields['业务反馈问题记录表']}`);
      // 继续转发流程
      return this.handleFeedback(event, text, '问题', config);
    } else {
      console.log('  未找到记录，创建新记录');
      // 作为新反馈处理
      return this.handleFeedback(event, text, '问题', config);
    }
  }

  /**
   * 处理功能咨询
   */
  private async handleConsultation(
    event: FeishuMessageEvent,
    text: string,
    config: ForwardConfig
  ): Promise<any> {
    const result = await this.forwarder.forwardMessage({
      sourceChat: config.source_name,
      reporter: event.sender.sender_name || 'Unknown',
      content: text,
      messageType: '咨询',
      sourceChatId: event.chat_id,
      messageId: event.message_id,
      recordBitable: false
    });

    return {
      handled: true,
      type: 'consultation',
      forwarded: result.success,
      result
    };
  }

  /**
   * 处理问题/需求反馈
   */
  private async handleFeedback(
    event: FeishuMessageEvent,
    text: string,
    messageType: MessageType,
    config: ForwardConfig
  ): Promise<any> {
    // 1. 转发消息
    const forwardResult = await this.forwarder.forwardMessage({
      sourceChat: config.source_name,
      reporter: event.sender.sender_name || 'Unknown',
      content: text,
      messageType: messageType,
      sourceChatId: event.chat_id,
      messageId: event.message_id,
      recordBitable: config.record_bitable
    });

    if (!forwardResult.success) {
      return {
        handled: true,
        type: 'feedback',
        forwarded: false,
        error: forwardResult.error
      };
    }

    // 2. 记录到表格
    let recordId: string | null = null;
    if (config.record_bitable) {
      try {
        // 使用消息的实际时间（create_time 是秒级字符串，转为毫秒）
        const messageTimeMs = parseInt(event.create_time) * 1000;
        console.log(`  📝 使用消息时间: ${messageTimeMs} (${new Date(messageTimeMs).toISOString()})`);
        
        recordId = await this.bitable.createRecord({
          title: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
          feedbackTime: messageTimeMs,
          feedbackUser: event.sender.sender_name || 'Unknown',
          feedbackSource: config.source_name,
          content: text,
          sourceChatId: event.chat_id,
          type: messageType as '问题' | '需求',
          originalMessageId: event.message_id
        });
        console.log(`  ✅ 已记录到表格: ${recordId}`);
      } catch (e) {
        console.error(`  ⚠️ 记录表格失败: ${e}`);
      }
    }

    return {
      handled: true,
      type: 'feedback',
      forwarded: true,
      recordId,
      result: forwardResult
    };
  }

  /**
   * 提取关键词
   */
  private extractKeywords(text: string): string[] {
    const commonKeywords = [
      '同步', '数据', '订单', '导入', 'CSV', '派卡', '公众号',
      '通知', '抢单', '交付', '系统', '接口', '历史订单',
      '重新同步', '统计', '配置', '关闭', '统计', '登录',
      '报错', '故障', '异常', 'bug', '问题'
    ];
    
    return commonKeywords.filter(kw => text.includes(kw));
  }

  /**
   * 处理状态更新（来自目标群的回复）
   */
  async handleStatusUpdate(event: FeishuMessageEvent): Promise<any> {
    // 检查是否@我
    if (!this.isAtMe(event)) {
      return { handled: false, reason: 'not_at_me' };
    }

    let textContent = '';
    try {
      const content = JSON.parse(event.content);
      textContent = content.text || '';
    } catch {
      textContent = event.content;
    }

    const cleanText = removeAtTags(textContent);
    const senderName = event.sender.sender_name || '处理人';

    console.log(`[${new Date().toISOString()}] 收到状态更新 from ${senderName}`);
    console.log(`  内容: ${cleanText.substring(0, 50)}...`);

    await this.getToken();

    // 提取状态和处理结果
    const { status, result } = this.extractStatusAndResult(cleanText);
    if (!status) {
      console.log('  未识别到状态，使用默认"已解决"');
    }

    // 提取关键词
    const keywords = this.extractKeywords(cleanText);
    if (keywords.length === 0) {
      return { handled: false, reason: 'no_keywords' };
    }

    // 查找匹配的记录
    const matchedRecord = await this.bitable.findRecordByKeywords(keywords);
    if (!matchedRecord) {
      console.log('  未找到匹配的记录');
      return { handled: false, reason: 'no_matched_record' };
    }

    console.log(`  匹配到: ${matchedRecord.fields['业务反馈问题记录表']}`);

    // 更新状态
    const updateSuccess = await this.bitable.updateRecordStatus(
      matchedRecord.record_id,
      status || '已解决',
      result
    );

    if (updateSuccess) {
      console.log(`  ✅ 已更新状态为: ${status}`);
      
      // 转发回复到来源群
      const forwardSuccess = await this.forwarder.forwardReplyToSource({
        matchedRecord,
        status: status || '已解决',
        result,
        senderName
      });

      return {
        handled: true,
        type: 'status_update',
        updated: true,
        forwarded: forwardSuccess,
        recordId: matchedRecord.record_id
      };
    }

    return {
      handled: true,
      type: 'status_update',
      updated: false
    };
  }

  /**
   * 从消息中提取状态和处理结果
   */
  private extractStatusAndResult(text: string): { status: string | null; result: string } {
    const statusKeywords: Record<string, string[]> = {
      '已解决': ['已解决', '已完成', '搞定', '已修复', 'ok', 'OK', '已处理', '解决了', '完成了', '处理好了', '同步好了', '已上线', '上线'],
      '已关闭': ['已关闭', '无需处理', '重复问题'],
      '处理中': ['处理中', '正在处理', '跟进中'],
      '待处理': ['待处理']
    };

    for (const [status, keywords] of Object.entries(statusKeywords)) {
      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          // 提取包含关键字的句子
          const sentences = text.split(/[。！？\n]/);
          for (const sent of sentences) {
            if (sent.includes(keyword)) {
              return { status, result: sent.trim() };
            }
          }
          return { status, result: text.substring(0, 100) };
        }
      }
    }

    return { status: null, result: text.substring(0, 100) };
  }
}

// 导出默认实例
export default FeedbackHandler;

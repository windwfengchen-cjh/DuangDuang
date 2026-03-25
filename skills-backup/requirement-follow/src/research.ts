/**
 * 调研群消息处理模块
 */

import * as fs from 'fs';
import * as path from 'path';

const RESEARCH_STATE_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research');
const RESEARCH_MESSAGES_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research_messages');
const PRD_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'prd');

[RESEARCH_STATE_DIR, RESEARCH_MESSAGES_DIR, PRD_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
});

export interface FeishuMessageEvent {
  message_id: string;
  chat_id: string;
  chat_type: 'group' | 'p2p';
  sender: { sender_id: { open_id: string }; sender_type: string; sender_name?: string };
  message_type: string;
  content: string;
  mentions?: Array<{ key: string; id: { open_id: string }; name: string }>;
  create_time: string;
  update_time: string;
}

export interface ChatMessage {
  message_id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  message_type: string;
  create_time: string;
  is_requirement_person: boolean;
}

export type ResearchMode = 'auto_collect' | 'qa' | 'hybrid';

export interface ResearchSession {
  chat_id: string;
  requirement_title: string;
  requirement_person_id: string;
  requirement_person_name: string;
  boss_id: string;
  record_id?: string;
  current_question_idx: number;
  collected_data: Record<string, string>;
  attachments: string[];
  status: 'waiting' | 'waiting_start' | 'collecting' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
  last_message_time?: string;
  message_count: number;
  mode: ResearchMode;
  auto_collect_mode: boolean;
  enable_qa: boolean;
  enable_auto_collect: boolean;
  waiting_for_answer?: boolean;
  auto_collect_deadline?: string;
  processed_message_ids: string[];
}

export const RESEARCH_QUESTIONS = [
  {
    key: 'background',
    question: '👋 需求调研开始！\n\n📋 **需求**: {title}\n👤 **需求人**: @{requester}\n\n**问题 1/7：业务背景**\n请描述需求的业务背景和产生场景。',
    required: true,
    prd_section: '背景与目标'
  },
  {
    key: 'target_users',
    question: '**问题 2/7：目标用户**\n这个需求的目标用户是谁？',
    required: true,
    prd_section: '背景与目标'
  },
  {
    key: 'current_situation',
    question: '**问题 3/7：现状描述**\n请描述当前的系统/流程现状。',
    required: true,
    prd_section: '现状'
  },
  {
    key: 'pain_points',
    question: '**问题 4/7：核心痛点**\n当前的核心痛点是什么？',
    required: true,
    prd_section: '现状'
  },
  {
    key: 'expected_solution',
    question: '**问题 5/7：期望解决方案**\n您期望的解决方案是什么？',
    required: true,
    prd_section: '方案'
  },
  {
    key: 'priority',
    question: '**问题 6/7：优先级和时间**\n需求的优先级和时间要求是怎样的？',
    required: true,
    prd_section: '优先级和时间计划'
  },
  {
    key: 'attachments',
    question: '**问题 7/7：相关资料**\n是否有相关数据、截图、文档需要补充？',
    required: false,
    prd_section: '附件与参考资料'
  }
];

export function formatQuestion(template: string, title: string, requester: string): string {
  return template.replace(/\{title\}/g, title).replace(/\{requester\}/g, requester);
}

function getStateFilePath(chatId: string): string {
  return path.join(RESEARCH_STATE_DIR, `${chatId}.json`);
}

function getMessagesFilePath(chatId: string): string {
  return path.join(RESEARCH_MESSAGES_DIR, `${chatId}.json`);
}

export function loadResearchSession(chatId: string): ResearchSession | null {
  try {
    const data = fs.readFileSync(getStateFilePath(chatId), 'utf-8');
    return JSON.parse(data);
  } catch { return null; }
}

export function saveResearchSession(session: ResearchSession): void {
  session.updated_at = new Date().toISOString();
  fs.writeFileSync(getStateFilePath(session.chat_id), JSON.stringify(session, null, 2), 'utf-8');
}

export function deleteResearchSession(chatId: string): void {
  try { fs.unlinkSync(getStateFilePath(chatId)); } catch {}
  try { fs.unlinkSync(getMessagesFilePath(chatId)); } catch {}
}

export function loadChatMessages(chatId: string): ChatMessage[] {
  try {
    return JSON.parse(fs.readFileSync(getMessagesFilePath(chatId), 'utf-8'));
  } catch { return []; }
}

export function saveChatMessages(chatId: string, messages: ChatMessage[]): void {
  fs.writeFileSync(getMessagesFilePath(chatId), JSON.stringify(messages, null, 2), 'utf-8');
}

export function addChatMessage(chatId: string, message: ChatMessage): void {
  const messages = loadChatMessages(chatId);
  if (!messages.some(m => m.message_id === message.message_id)) {
    messages.push(message);
    saveChatMessages(chatId, messages);
  }
}

export function isResearchChat(chatId: string): boolean {
  return loadResearchSession(chatId) !== null;
}

export function isAutoCollectExpired(session: ResearchSession): boolean {
  return session.auto_collect_deadline ? new Date() > new Date(session.auto_collect_deadline) : false;
}

function extractTextFromEvent(event: FeishuMessageEvent): string {
  try {
    const content = JSON.parse(event.content);
    if (content.text) return content.text;
    if (content.post?.zh_cn) {
      let text = content.post.zh_cn.title || '';
      for (const block of content.post.zh_cn.content || []) {
        for (const item of block) {
          if (item.tag === 'text') text += item.text;
          if (item.tag === 'at') text += `@${item.user_name}`;
        }
      }
      return text;
    }
  } catch {}
  return event.content;
}

async function sendFeishuMessage(chatId: string, text: string, token: string): Promise<boolean> {
  try {
    const res = await fetch('https://open.feishu.cn/open-apis/im/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ receive_id: chatId, msg_type: 'text', content: JSON.stringify({ text }) })
    });
    const data = await res.json() as { code: number };
    return data.code === 0;
  } catch { return false; }
}

export function createResearchSession(
  chatId: string, title: string, personId: string, personName: string, bossId: string,
  recordId?: string, mode: ResearchMode = 'hybrid', hours: number = 24
): ResearchSession {
  const now = new Date();
  const isAuto = mode === 'auto_collect' || mode === 'hybrid';
  const isQa = mode === 'qa' || mode === 'hybrid';
  const session: ResearchSession = {
    chat_id: chatId, requirement_title: title, requirement_person_id: personId,
    requirement_person_name: personName, boss_id: bossId, record_id: recordId,
    current_question_idx: 0, collected_data: {}, attachments: [], status: 'waiting_start',
    created_at: now.toISOString(), updated_at: now.toISOString(), message_count: 0,
    mode, auto_collect_mode: isAuto, enable_qa: isQa, enable_auto_collect: isAuto,
    auto_collect_deadline: new Date(now.getTime() + hours * 3600000).toISOString(),
    processed_message_ids: []
  };
  saveResearchSession(session);
  return session;
}

export async function startResearch(chatId: string, token: string): Promise<boolean> {
  const session = loadResearchSession(chatId);
  if (!session) return false;

  const deadline = session.auto_collect_deadline ? new Date(session.auto_collect_deadline).toLocaleString('zh-CN') : '24小时后';
  
  // 统一的欢迎消息，等待"开始调研"指令
  const welcome = `👋 需求调研群已创建！
📋 **需求**: ${session.requirement_title}
👤 **需求人**: ${session.requirement_person_name}

🤖 **自动收集模式已启动**：
• 我会自动收集群内所有消息用于生成PRD
• 发送"开始调研"启动7个问题的引导流程
• 发送"完成调研"或"生成PRD"结束调研
• 发送"取消"终止调研

⏰ 截止时间: ${deadline}`;

  await sendFeishuMessage(chatId, welcome, token);

  // 状态保持为 waiting_start，等待"开始调研"指令
  // 不发送第一个问题，由用户触发
  saveResearchSession(session);
  return true;
}

async function generatePRD(session: ResearchSession, token: string): Promise<void> {
  await sendFeishuMessage(session.chat_id, '📝 正在生成PRD文档...', token);
  const messages = loadChatMessages(session.chat_id);

  let content = `# ${session.requirement_title} - PRD\n\n**需求人**: ${session.requirement_person_name}\n**消息数**: ${messages.length}条\n**模式**: ${session.mode}\n\n`;

  if (session.enable_qa && Object.keys(session.collected_data).length > 0) {
    content += '## 问答记录\n\n';
    for (const q of RESEARCH_QUESTIONS) {
      if (session.collected_data[q.key]) {
        content += `**${q.prd_section}**: ${session.collected_data[q.key]}\n\n`;
      }
    }
  }

  content += '## 群聊记录\n\n';
  for (const m of messages) {
    content += `**${m.sender_name}**${m.is_requirement_person ? '【需求人】' : ''} (${new Date(m.create_time).toLocaleString('zh-CN')}): ${m.content}\n\n`;
  }

  const filename = `${session.requirement_title.slice(0, 30).replace(/[^\w\u4e00-\u9fa5]/g, '_')}_${Date.now()}.md`;
  const filepath = path.join(PRD_DIR, filename);
  fs.writeFileSync(filepath, content, 'utf-8');

  await sendFeishuMessage(session.chat_id, `✅ PRD已生成！\n📄 文件: ${filepath}\n\n本群将在3秒后解散。`, token);
}

export async function handleResearchMessage(event: FeishuMessageEvent, token: string): Promise<{ handled: boolean; result?: any }> {
  const chatId = event.chat_id;
  const senderId = event.sender.sender_id.open_id;
  const senderName = event.sender.sender_name || 'Unknown';

  const session = loadResearchSession(chatId);
  if (!session) return { handled: false };
  if (session.status === 'completed' || session.status === 'cancelled') return { handled: false, result: { reason: 'session_ended' } };

  const text = extractTextFromEvent(event);
  const isReqPerson = senderId === session.requirement_person_id;
  const isBoss = senderId === session.boss_id;

  // 保存消息
  addChatMessage(chatId, { message_id: event.message_id, sender_id: senderId, sender_name: senderName, content: text, message_type: event.message_type, create_time: Date.now().toString(), is_requirement_person: isReqPerson });
  session.message_count++;
  session.last_message_time = new Date().toISOString();
  saveResearchSession(session);

  // 指令处理
  const startKeywords = ['开始调研', '启动调研', '开始', '启动'];
  const completeKeywords = ['完成调研', '结束调研', '调研完成', '生成PRD', '完成'];
  const cancelKeywords = ['取消', '不做了', '停止'];
  const isStart = startKeywords.some(k => text.includes(k));
  const isComplete = completeKeywords.some(k => text.includes(k));
  const isCancel = cancelKeywords.some(k => text.includes(k));
  const isExpired = isAutoCollectExpired(session);

  // 处理取消指令
  if (isCancel && (isReqPerson || isBoss)) {
    session.status = 'cancelled';
    saveResearchSession(session);
    await sendFeishuMessage(chatId, '❌ 需求调研已取消。', token);
    return { handled: true, result: { action: 'cancelled' } };
  }

  // 处理开始调研指令（仅在 waiting_start 状态）
  if (isStart && session.status === 'waiting_start' && (isReqPerson || isBoss)) {
    session.status = 'collecting';
    saveResearchSession(session);
    await sendFeishuMessage(chatId, '🚀 调研开始！请回答以下问题：', token);
    // 发送第一个问题
    if (session.enable_qa) {
      await sendFeishuMessage(chatId, formatQuestion(RESEARCH_QUESTIONS[0].question, session.requirement_title, session.requirement_person_name), token);
      session.current_question_idx = 0;
      saveResearchSession(session);
    }
    return { handled: true, result: { action: 'started' } };
  }

  // 处理完成/生成PRD指令
  if (isComplete || isExpired) {
    if (isExpired) await sendFeishuMessage(chatId, '⏰ 自动收集时间到，正在生成PRD...', token);
    session.status = 'completed';
    saveResearchSession(session);
    await generatePRD(session, token);
    return { handled: true, result: { action: 'completed' } };
  }

  // 自动收集模式
  if (session.auto_collect_mode && !session.enable_qa) {
    if (session.message_count % 10 === 0) {
      await sendFeishuMessage(chatId, `✅ 已收集 ${session.message_count} 条消息`, token);
    }
    return { handled: true, result: { action: 'collected', mode: 'auto' } };
  }

  // 问答模式只处理需求人回复
  if (session.enable_qa && !isReqPerson) {
    return { handled: true, result: { action: 'ignored' } };
  }

  if (session.enable_qa) {
    const currentQ = RESEARCH_QUESTIONS[session.current_question_idx];
    if (currentQ) session.collected_data[currentQ.key] = text;
    session.current_question_idx++;

    if (session.current_question_idx < RESEARCH_QUESTIONS.length) {
      await sendFeishuMessage(chatId, formatQuestion(RESEARCH_QUESTIONS[session.current_question_idx].question, session.requirement_title, session.requirement_person_name), token);
      saveResearchSession(session);
      return { handled: true, result: { action: 'next_question' } };
    } else {
      session.status = 'completed';
      saveResearchSession(session);
      await generatePRD(session, token);
      return { handled: true, result: { action: 'completed' } };
    }
  }

  return { handled: true, result: { action: 'collected' } };
}

export function getResearchStats(chatId: string): { messageCount: number; status: string } | null {
  const session = loadResearchSession(chatId);
  return session ? { messageCount: session.message_count || 0, status: session.status } : null;
}

export class ResearchHandler {
  private token: string;
  constructor(token: string) { this.token = token; }
  async handleMessage(event: FeishuMessageEvent) { return handleResearchMessage(event, this.token); }
  isResearchChat(chatId: string) { return isResearchChat(chatId); }
  getStats(chatId: string) { return getResearchStats(chatId); }
}

export default ResearchHandler;

// ==================== 消息轮询机制 ====================

import { FeishuAPI } from './api';

interface PollOptions {
  intervalMs?: number;      // 轮询间隔（毫秒）
  onMessage?: (chatId: string, result: any) => void;  // 消息处理回调
  onError?: (chatId: string, error: Error) => void;   // 错误回调
}

/**
 * 获取所有活跃的调研会话
 */
export function getActiveResearchSessions(): ResearchSession[] {
  const sessions: ResearchSession[] = [];
  try {
    if (!fs.existsSync(RESEARCH_STATE_DIR)) return sessions;
    const files = fs.readdirSync(RESEARCH_STATE_DIR);
    for (const file of files) {
      if (!file.endsWith('.json')) continue;
      const chatId = file.replace('.json', '');
      const session = loadResearchSession(chatId);
      // 包含 collecting 和 waiting_start 状态的会话
      if (session && (session.status === 'collecting' || session.status === 'waiting_start')) {
        sessions.push(session);
      }
    }
  } catch (e) {
    console.error('获取活跃会话失败:', e);
  }
  return sessions;
}

/**
 * 轮询单个调研群的消息
 * @param chatId 群ID
 * @param api FeishuAPI 实例
 * @param options 轮询选项
 * @returns 是否启动成功
 */
export async function pollResearchChat(
  chatId: string, 
  api: FeishuAPI, 
  options?: PollOptions
): Promise<boolean> {
  const session = loadResearchSession(chatId);
  if (!session) {
    console.log(`[${chatId}] 未找到调研会话，跳过轮询`);
    return false;
  }
  
  // 允许 collecting 和 waiting_start 状态进行轮询
  if (session.status !== 'collecting' && session.status !== 'waiting_start') {
    console.log(`[${chatId}] 会话状态为 ${session.status}，停止轮询`);
    return false;
  }

  try {
    const token = await api.getTenantAccessToken();
    
    // 获取消息历史（从上次检查时间开始）
    const startTime = session.last_message_time || session.created_at;
    const messages = await api.getChatMessages(chatId, { 
      startTime,
      pageSize: 20 
    });
    
    if (messages.length === 0) {
      return true; // 没有新消息，继续轮询
    }

    console.log(`[${chatId}] 获取到 ${messages.length} 条新消息`);

    // 处理每条消息
    for (const msg of messages) {
      // 跳过已处理的消息
      if (session.processed_message_ids?.includes(msg.message_id)) {
        continue;
      }
      
      // 跳过机器人自己的消息
      const botId = await getBotOpenId(api);
      if (msg.sender.sender_id.open_id === botId) {
        session.processed_message_ids = session.processed_message_ids || [];
        session.processed_message_ids.push(msg.message_id);
        continue;
      }

      // 构建消息事件
      const event: FeishuMessageEvent = {
        message_id: msg.message_id,
        chat_id: msg.chat_id,
        chat_type: 'group',
        sender: {
          sender_id: { open_id: msg.sender.sender_id.open_id },
          sender_type: msg.sender.sender_type,
          sender_name: undefined // API 返回的消息没有 sender_name，需要通过其他方式获取
        },
        message_type: msg.msg_type,
        content: msg.content,
        mentions: msg.mentions,
        create_time: msg.create_time,
        update_time: msg.update_time
      };

      // 处理消息
      const result = await handleResearchMessage(event, token);
      
      // 记录已处理
      session.processed_message_ids = session.processed_message_ids || [];
      session.processed_message_ids.push(msg.message_id);
      
      // 回调通知
      if (options?.onMessage) {
        options.onMessage(chatId, result);
      }
    }

    // 更新会话状态
    const updatedSession = loadResearchSession(chatId);
    if (updatedSession) {
      updatedSession.last_message_time = new Date().toISOString();
      saveResearchSession(updatedSession);
    }

    return true;
  } catch (error) {
    console.error(`[${chatId}] 轮询失败:`, error);
    if (options?.onError) {
      options.onError(chatId, error as Error);
    }
    return false;
  }
}

/**
 * 启动持续轮询所有活跃调研群
 * @param api FeishuAPI 实例
 * @param options 轮询选项
 * @returns 停止轮询的函数
 */
export function startResearchPolling(
  api: FeishuAPI, 
  options?: PollOptions
): { stop: () => void; isRunning: () => boolean } {
  const intervalMs = options?.intervalMs || 5000; // 默认5秒
  let running = true;
  let pollTimer: NodeJS.Timeout | null = null;

  const doPoll = async () => {
    if (!running) return;
    
    const sessions = getActiveResearchSessions();
    console.log(`[轮询] 发现 ${sessions.length} 个活跃调研会话`);
    
    for (const session of sessions) {
      if (!running) break;
      await pollResearchChat(session.chat_id, api, options);
    }

    if (running) {
      pollTimer = setTimeout(doPoll, intervalMs);
    }
  };

  // 启动第一次轮询
  doPoll();

  return {
    stop: () => {
      running = false;
      if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
      }
      console.log('[轮询] 已停止');
    },
    isRunning: () => running
  };
}

/**
 * 获取机器人的 OpenID
 */
async function getBotOpenId(api: FeishuAPI): Promise<string | null> {
  try {
    const token = await api.getTenantAccessToken();
    const response = await fetch('https://open.feishu.cn/open-apis/bot/v3/info', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json() as any;
    if (data.code === 0 && data.data?.bot?.open_id) {
      return data.data.bot.open_id;
    }
    return null;
  } catch {
    return null;
  }
}

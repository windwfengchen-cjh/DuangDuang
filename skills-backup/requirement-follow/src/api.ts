/**
 * Feishu API 封装模块
 * 封装飞书开放平台 API 调用
 */

export interface FeishuConfig {
  appId: string;
  appSecret: string;
  baseUrl?: string;
}

export interface FeishuResponse<T = any> {
  code: number;
  msg: string;
  data?: T;
  error?: any;
}

export interface ChatInfo {
  chat_id: string;
  name: string;
  description?: string;
}

export interface AddMemberResult {
  user_id: string;
  success: boolean;
  already_in_chat: boolean;
  error_code?: number;
  error_msg?: string;
}

export interface AddMembersSummary {
  overall_success: boolean;
  added: string[];
  already_in_chat: string[];
  failed: Array<{ user_id: string; error_code?: number; error_msg?: string }>;
  results: AddMemberResult[];
}

export interface MemberValidationResult {
  valid: boolean;
  member_count: number;
  expected_count: number;
  disbanded: boolean;
  error?: string;
}

export class FeishuAPI {
  private config: FeishuConfig;
  private token: string | null = null;
  private tokenExpiry: number = 0;

  constructor(config: FeishuConfig) {
    this.config = { baseUrl: 'https://open.feishu.cn/open-apis', ...config };
  }

  async getTenantAccessToken(): Promise<string> {
    const now = Date.now();
    if (this.token && now < this.tokenExpiry) return this.token;

    const url = `${this.config.baseUrl}/auth/v3/tenant_access_token/internal`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_id: this.config.appId, app_secret: this.config.appSecret })
    });

    const data = await response.json() as any;
    if (data.code !== 0) throw new Error(`获取 token 失败: ${data.msg}`);
    
    // 飞书 API 响应格式: tenant_access_token 直接在根级别
    const token = data.tenant_access_token || data.data?.tenant_access_token;
    const expire = data.expire || data.data?.expire;
    
    if (!token) throw new Error(`获取 token 失败: 响应数据不完整`);

    this.token = token;
    this.tokenExpiry = now + (expire || 1.5 * 60 * 60) * 1000;
    return token;
  }

  getCurrentToken(): string | null { return this.token; }

  private async getHeaders(): Promise<Record<string, string>> {
    return { 'Authorization': `Bearer ${await this.getTenantAccessToken()}`, 'Content-Type': 'application/json' };
  }

  async createChat(params: { name: string; description?: string; chat_mode?: 'group' | 'p2p'; chat_type?: 'public' | 'private'; user_id_list?: string[] }): Promise<ChatInfo> {
    const url = `${this.config.baseUrl}/im/v1/chats`;
    const headers = await this.getHeaders();
    const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify({ ...params, chat_mode: params.chat_mode || 'group', chat_type: params.chat_type || 'private' }) });
    const data = await response.json() as FeishuResponse<{ chat_id: string; name: string }>;
    if (data.code !== 0) throw new Error(`创建群聊失败: ${data.msg} (code: ${data.code})`);
    return { chat_id: data.data!.chat_id, name: data.data!.name, description: params.description };
  }

  async getChatInfo(chatId: string): Promise<ChatInfo | null> {
    const url = `${this.config.baseUrl}/im/v1/chats/${chatId}`;
    try {
      const response = await fetch(url, { headers: await this.getHeaders() });
      const data = await response.json() as FeishuResponse<{ name: string; description?: string }>;
      if (data.code === 0 && data.data) return { chat_id: chatId, name: data.data.name, description: data.data.description };
    } catch (e) { console.error('获取群信息失败:', e); }
    return null;
  }

  async disbandChat(chatId: string): Promise<boolean> {
    const url = `${this.config.baseUrl}/im/v1/chats/${chatId}`;
    try {
      const response = await fetch(url, { method: 'DELETE', headers: await this.getHeaders() });
      const data = await response.json() as FeishuResponse;
      if (data.code === 0) { console.log(`✅ 群 ${chatId} 已解散`); return true; }
      console.error(`❌ 解散群失败: ${data.msg}`); return false;
    } catch (e) { console.error(`❌ 解散群异常:`, e); return false; }
  }

  async getChatMembers(chatId: string): Promise<Set<string>> {
    const url = `${this.config.baseUrl}/im/v1/chats/${chatId}/members?member_id_type=open_id&page_size=100`;
    const memberIds = new Set<string>();
    try {
      const response = await fetch(url, { headers: await this.getHeaders() });
      const data = await response.json() as FeishuResponse<{ items: Array<{ member_id: string }> }>;
      if (data.code === 0 && data.data) data.data.items.forEach(m => { if (m.member_id) memberIds.add(m.member_id); });
    } catch (e) { console.error('获取群成员失败:', e); }
    return memberIds;
  }

  async addSingleMember(chatId: string, userId: string, maxRetries: number = 3): Promise<AddMemberResult> {
    const result: AddMemberResult = { user_id: userId, success: false, already_in_chat: false };
    const url = `${this.config.baseUrl}/im/v1/chats/${chatId}/members`;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ member_id_type: 'open_id', members: [{ member_id: userId, member_role: 'member' }] }) });
        const data = await response.json() as FeishuResponse;
        if (data.code === 0) { result.success = true; return result; }
        if (data.code === 112516) { result.success = true; result.already_in_chat = true; return result; }
        if ([112515, 11200, 11201, 11202].includes(data.code)) { result.error_code = data.code; result.error_msg = data.msg; return result; }
        result.error_code = data.code; result.error_msg = data.msg;
        if (attempt < maxRetries - 1) await new Promise(r => setTimeout(r, (attempt + 1) * 3000));
      } catch (e) { result.error_msg = String(e); if (attempt < maxRetries - 1) await new Promise(r => setTimeout(r, 2000)); }
    }
    return result;
  }

  async addMembersToChat(chatId: string, userIds: string[], options?: { skipExisting?: boolean; delayMs?: number }): Promise<AddMembersSummary> {
    const summary: AddMembersSummary = { overall_success: false, added: [], already_in_chat: [], failed: [], results: [] };
    const validUserIds = userIds.filter(id => id); if (validUserIds.length === 0) return summary;
    let membersToAdd = validUserIds;
    if (options?.skipExisting !== false) {
      const existing = await this.getChatMembers(chatId);
      membersToAdd = validUserIds.filter(id => { if (existing.has(id)) { summary.already_in_chat.push(id); return false; } return true; });
    }
    if (membersToAdd.length === 0) { summary.overall_success = true; return summary; }
    const delay = options?.delayMs || 500;
    for (let i = 0; i < membersToAdd.length; i++) {
      const result = await this.addSingleMember(chatId, membersToAdd[i]);
      summary.results.push(result);
      if (result.success) { if (result.already_in_chat) summary.already_in_chat.push(membersToAdd[i]); else summary.added.push(membersToAdd[i]); }
      else summary.failed.push({ user_id: membersToAdd[i], error_code: result.error_code, error_msg: result.error_msg });
      if (i < membersToAdd.length - 1) await new Promise(r => setTimeout(r, delay));
    }
    summary.overall_success = summary.added.length > 0 || summary.failed.length === 0;
    return summary;
  }

  async validateChatMembers(chatId: string, expectedUserIds: string[], options?: { autoDisbandOnEmpty?: boolean }): Promise<MemberValidationResult> {
    const result: MemberValidationResult = { valid: false, member_count: 0, expected_count: expectedUserIds.length, disbanded: false };
    const memberIds = await this.getChatMembers(chatId); result.member_count = memberIds.size;
    if (memberIds.size === 0) {
      result.error = '群成员数量为0，群创建失败';
      if (options?.autoDisbandOnEmpty !== false) result.disbanded = await this.disbandChat(chatId);
      return result;
    }
    result.valid = true; return result;
  }

  async sendTextMessage(receiveId: string, text: string, options?: { receiveIdType?: 'chat_id' | 'open_id' }): Promise<boolean> {
    const url = `${this.config.baseUrl}/im/v1/messages?receive_id_type=${options?.receiveIdType || 'chat_id'}`;
    try {
      const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ receive_id: receiveId, msg_type: 'text', content: JSON.stringify({ text }) }) });
      const data = await response.json() as FeishuResponse;
      return data.code === 0;
    } catch (e) { console.error('发送消息失败:', e); return false; }
  }

  async sendPostMessage(receiveId: string, postContent: { title: string; content: Array<Array<{ tag: string; text?: string; user_id?: string; user_name?: string; href?: string }>> }, options?: { receiveIdType?: 'chat_id' | 'open_id' }): Promise<boolean> {
    const url = `${this.config.baseUrl}/im/v1/messages?receive_id_type=${options?.receiveIdType || 'chat_id'}`;
    const content = { zh_cn: { title: postContent.title, content: postContent.content } };
    try {
      const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ receive_id: receiveId, msg_type: 'post', content: JSON.stringify(content) }) });
      const data = await response.json() as FeishuResponse;
      if (data.code !== 0) console.error('发送富文本消息失败:', data);
      return data.code === 0;
    } catch (e) { console.error('发送富文本消息异常:', e); return false; }
  }

  async sendWelcomeMessage(chatId: string, requirementContent: string, requesterName: string, requesterId: string): Promise<boolean> {
    const content = {
      title: '【需求调研开始】',
      content: [
        [{ tag: 'text', text: '🎯 需求调研群已创建' }], [{ tag: 'text', text: '' }],
        [{ tag: 'text', text: `需求方：${requesterName}` }],
        [{ tag: 'text', text: `需求摘要：${requirementContent.slice(0, 50)}...` }], [{ tag: 'text', text: '' }],
        [{ tag: 'text', text: '📋 请补充以下信息：' }],
        [{ tag: 'text', text: '• 需求的背景和目的' }],
        [{ tag: 'text', text: '• 期望的功能和效果' }],
        [{ tag: 'text', text: '• 涉及的用户场景' }],
        [{ tag: 'at', user_id: requesterId, user_name: requesterName }, { tag: 'text', text: ' 请开始补充~' }]
      ]
    };
    return this.sendPostMessage(chatId, content);
  }

  async sendDisbandNotice(chatId: string): Promise<boolean> {
    const content = {
      title: '【需求跟进完成】',
      content: [
        [{ tag: 'text', text: '✅ 需求调研已完成，PRD文档已生成' }],
        [{ tag: 'text', text: '' }],
        [{ tag: 'text', text: '本群将在3秒后自动解散' }],
        [{ tag: 'text', text: '感谢各位的配合！' }]
      ]
    };
    return this.sendPostMessage(chatId, content);
  }

  async sendChatInvite(userId: string, chatId: string, chatName: string, options?: { userName?: string }): Promise<boolean> {
    const content = {
      title: `【邀请加入${chatName}】`,
      content: [
        [{ tag: 'text', text: `👋 您好${options?.userName ? `，${options.userName}` : ''}！` }],
        [{ tag: 'text', text: '' }],
        [{ tag: 'text', text: '系统无法自动将您添加到需求调研群，请通过以下链接加入：' }],
        [{ tag: 'text', text: '' }],
        [{ tag: 'a', text: '👉 点击加入群聊', href: `https://applink.feishu.cn/client/chat/open?chat_id=${chatId}` }],
        [{ tag: 'text', text: '' }],
        [{ tag: 'text', text: '如链接无法打开，请在飞书中搜索群ID进入：' }],
        [{ tag: 'text', text: chatId }]
      ]
    };
    return this.sendPostMessage(userId, content, { receiveIdType: 'open_id' });
  }

  /**
   * 获取群消息历史
   * @param chatId 群ID
   * @param options 查询选项
   * @returns 消息列表
   */
  async getChatMessages(chatId: string, options?: { 
    containerId?: string; 
    startTime?: string; 
    endTime?: string; 
    pageSize?: number;
  }): Promise<Array<{
    message_id: string;
    chat_id: string;
    sender: { sender_id: { open_id: string }; sender_type: string; };
    content: string;
    msg_type: string;
    create_time: string;
    update_time: string;
    mentions?: Array<any>;
  }>> {
    const pageSize = options?.pageSize || 50;
    let url = `${this.config.baseUrl}/im/v1/messages?container_id_type=chat&container_id=${chatId}&page_size=${pageSize}`;
    
    if (options?.startTime) url += `&start_time=${encodeURIComponent(options.startTime)}`;
    if (options?.endTime) url += `&end_time=${encodeURIComponent(options.endTime)}`;
    
    try {
      const response = await fetch(url, { headers: await this.getHeaders() });
      const data = await response.json() as FeishuResponse<{
        items: Array<{
          message_id: string;
          chat_id: string;
          sender: { sender_id: { open_id: string }; sender_type: string; };
          body: { content: string };
          msg_type: string;
          create_time: string;
          update_time: string;
          mentions?: Array<any>;
        }>;
        has_more: boolean;
        page_token: string;
      }>;
      
      if (data.code !== 0) {
        console.error('获取群消息失败:', data.msg);
        return [];
      }
      
      return (data.data?.items || []).map(item => ({
        message_id: item.message_id,
        chat_id: item.chat_id,
        sender: item.sender,
        content: item.body?.content || '{}',
        msg_type: item.msg_type,
        create_time: item.create_time,
        update_time: item.update_time,
        mentions: item.mentions
      }));
    } catch (e) {
      console.error('获取群消息异常:', e);
      return [];
    }
  }
}

export default FeishuAPI;

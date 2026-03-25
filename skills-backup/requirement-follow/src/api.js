"use strict";
/**
 * Feishu API 封装模块
 * 封装飞书开放平台 API 调用
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.FeishuAPI = void 0;
class FeishuAPI {
    constructor(config) {
        this.token = null;
        this.tokenExpiry = 0;
        this.config = { baseUrl: 'https://open.feishu.cn/open-apis', ...config };
    }
    async getTenantAccessToken() {
        const now = Date.now();
        if (this.token && now < this.tokenExpiry)
            return this.token;
        const url = `${this.config.baseUrl}/auth/v3/tenant_access_token/internal`;
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ app_id: this.config.appId, app_secret: this.config.appSecret })
        });
        const data = await response.json();
        if (data.code !== 0)
            throw new Error(`获取 token 失败: ${data.msg}`);
        this.token = data.data.tenant_access_token;
        this.tokenExpiry = now + 1.5 * 60 * 60 * 1000;
        return this.token;
    }
    getCurrentToken() { return this.token; }
    async getHeaders() {
        return { 'Authorization': `Bearer ${await this.getTenantAccessToken()}`, 'Content-Type': 'application/json' };
    }
    async createChat(params) {
        const url = `${this.config.baseUrl}/im/v1/chats`;
        const headers = await this.getHeaders();
        const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify({ ...params, chat_mode: params.chat_mode || 'group', chat_type: params.chat_type || 'private' }) });
        const data = await response.json();
        if (data.code !== 0)
            throw new Error(`创建群聊失败: ${data.msg} (code: ${data.code})`);
        return { chat_id: data.data.chat_id, name: data.data.name, description: params.description };
    }
    async getChatInfo(chatId) {
        const url = `${this.config.baseUrl}/im/v1/chats/${chatId}`;
        try {
            const response = await fetch(url, { headers: await this.getHeaders() });
            const data = await response.json();
            if (data.code === 0 && data.data)
                return { chat_id: chatId, name: data.data.name, description: data.data.description };
        }
        catch (e) {
            console.error('获取群信息失败:', e);
        }
        return null;
    }
    async disbandChat(chatId) {
        const url = `${this.config.baseUrl}/im/v1/chats/${chatId}`;
        try {
            const response = await fetch(url, { method: 'DELETE', headers: await this.getHeaders() });
            const data = await response.json();
            if (data.code === 0) {
                console.log(`✅ 群 ${chatId} 已解散`);
                return true;
            }
            console.error(`❌ 解散群失败: ${data.msg}`);
            return false;
        }
        catch (e) {
            console.error(`❌ 解散群异常:`, e);
            return false;
        }
    }
    async getChatMembers(chatId) {
        const url = `${this.config.baseUrl}/im/v1/chats/${chatId}/members?member_id_type=open_id&page_size=100`;
        const memberIds = new Set();
        try {
            const response = await fetch(url, { headers: await this.getHeaders() });
            const data = await response.json();
            if (data.code === 0 && data.data)
                data.data.items.forEach(m => { if (m.member_id)
                    memberIds.add(m.member_id); });
        }
        catch (e) {
            console.error('获取群成员失败:', e);
        }
        return memberIds;
    }
    async addSingleMember(chatId, userId, maxRetries = 3) {
        const result = { user_id: userId, success: false, already_in_chat: false };
        const url = `${this.config.baseUrl}/im/v1/chats/${chatId}/members`;
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ member_id_type: 'open_id', members: [{ member_id: userId, member_role: 'member' }] }) });
                const data = await response.json();
                if (data.code === 0) {
                    result.success = true;
                    return result;
                }
                if (data.code === 112516) {
                    result.success = true;
                    result.already_in_chat = true;
                    return result;
                }
                if ([112515, 11200, 11201, 11202].includes(data.code)) {
                    result.error_code = data.code;
                    result.error_msg = data.msg;
                    return result;
                }
                result.error_code = data.code;
                result.error_msg = data.msg;
                if (attempt < maxRetries - 1)
                    await new Promise(r => setTimeout(r, (attempt + 1) * 3000));
            }
            catch (e) {
                result.error_msg = String(e);
                if (attempt < maxRetries - 1)
                    await new Promise(r => setTimeout(r, 2000));
            }
        }
        return result;
    }
    async addMembersToChat(chatId, userIds, options) {
        const summary = { overall_success: false, added: [], already_in_chat: [], failed: [], results: [] };
        const validUserIds = userIds.filter(id => id);
        if (validUserIds.length === 0)
            return summary;
        let membersToAdd = validUserIds;
        if (options?.skipExisting !== false) {
            const existing = await this.getChatMembers(chatId);
            membersToAdd = validUserIds.filter(id => { if (existing.has(id)) {
                summary.already_in_chat.push(id);
                return false;
            } return true; });
        }
        if (membersToAdd.length === 0) {
            summary.overall_success = true;
            return summary;
        }
        const delay = options?.delayMs || 500;
        for (let i = 0; i < membersToAdd.length; i++) {
            const result = await this.addSingleMember(chatId, membersToAdd[i]);
            summary.results.push(result);
            if (result.success) {
                if (result.already_in_chat)
                    summary.already_in_chat.push(membersToAdd[i]);
                else
                    summary.added.push(membersToAdd[i]);
            }
            else
                summary.failed.push({ user_id: membersToAdd[i], error_code: result.error_code, error_msg: result.error_msg });
            if (i < membersToAdd.length - 1)
                await new Promise(r => setTimeout(r, delay));
        }
        summary.overall_success = summary.added.length > 0 || summary.failed.length === 0;
        return summary;
    }
    async validateChatMembers(chatId, expectedUserIds, options) {
        const result = { valid: false, member_count: 0, expected_count: expectedUserIds.length, disbanded: false };
        const memberIds = await this.getChatMembers(chatId);
        result.member_count = memberIds.size;
        if (memberIds.size === 0) {
            result.error = '群成员数量为0，群创建失败';
            if (options?.autoDisbandOnEmpty !== false)
                result.disbanded = await this.disbandChat(chatId);
            return result;
        }
        result.valid = true;
        return result;
    }
    async sendTextMessage(receiveId, text, options) {
        const url = `${this.config.baseUrl}/im/v1/messages?receive_id_type=${options?.receiveIdType || 'chat_id'}`;
        try {
            const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ receive_id: receiveId, msg_type: 'text', content: JSON.stringify({ text }) }) });
            const data = await response.json();
            return data.code === 0;
        }
        catch (e) {
            console.error('发送消息失败:', e);
            return false;
        }
    }
    async sendPostMessage(receiveId, postContent, options) {
        const url = `${this.config.baseUrl}/im/v1/messages?receive_id_type=${options?.receiveIdType || 'chat_id'}`;
        const content = { zh_cn: { title: postContent.title, content: postContent.content } };
        try {
            const response = await fetch(url, { method: 'POST', headers: await this.getHeaders(), body: JSON.stringify({ receive_id: receiveId, msg_type: 'post', content: JSON.stringify(content) }) });
            const data = await response.json();
            if (data.code !== 0)
                console.error('发送富文本消息失败:', data);
            return data.code === 0;
        }
        catch (e) {
            console.error('发送富文本消息异常:', e);
            return false;
        }
    }
    async sendWelcomeMessage(chatId, requirementContent, requesterName, requesterId) {
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
    async sendDisbandNotice(chatId) {
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
    async sendChatInvite(userId, chatId, chatName, options) {
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
}
exports.FeishuAPI = FeishuAPI;
exports.default = FeishuAPI;
//# sourceMappingURL=api.js.map
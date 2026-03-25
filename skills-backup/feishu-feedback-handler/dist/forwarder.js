"use strict";
/**
 * 消息转发逻辑模块
 * 从 auto_forward.py 移植
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Forwarder = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const axios_1 = __importDefault(require("axios"));
// 飞书 API 基础 URL
const FEISHU_API_BASE = 'https://open.feishu.cn/open-apis';
/**
 * 转发器类
 */
class Forwarder {
    constructor(config) {
        this.token = null;
        this.contacts = {};
        this.config = config;
        this.loadContacts();
    }
    /**
     * 设置 Token
     */
    setToken(token) {
        this.token = token;
    }
    /**
     * 获取按日期命名的日志文件路径
     */
    getLogFilePath() {
        const date = new Date().toISOString().split('T')[0]; // 2026-03-25
        return path.join(__dirname, '..', 'logs', `forward_payloads_${date}.jsonl`);
    }
    /**
     * 清理超过1天的旧日志文件
     */
    cleanupOldLogs() {
        const logDir = path.join(__dirname, '..', 'logs');
        if (!fs.existsSync(logDir))
            return;
        const files = fs.readdirSync(logDir);
        const now = Date.now();
        const maxAge = 1 * 24 * 60 * 60 * 1000; // 1天
        for (const file of files) {
            if (file.startsWith('forward_payloads_') && file.endsWith('.jsonl')) {
                const filePath = path.join(logDir, file);
                const stats = fs.statSync(filePath);
                if (now - stats.mtime.getTime() > maxAge) {
                    fs.unlinkSync(filePath);
                    console.log(`🗑️ 已清理旧日志: ${file}`);
                }
            }
        }
    }
    /**
     * 记录转发报文日志
     */
    logForwardPayload(chatId, title, payload, response) {
        try {
            // 每次记录时检查并清理旧日志
            this.cleanupOldLogs();
            const logFile = this.getLogFilePath();
            const logDir = path.dirname(logFile);
            if (!fs.existsSync(logDir)) {
                fs.mkdirSync(logDir, { recursive: true });
            }
            const logEntry = {
                timestamp: new Date().toISOString(),
                chatId,
                title,
                payload,
                response
            };
            fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
        }
        catch (e) {
            console.warn('⚠️ 记录日志失败:', e);
        }
    }
    /**
     * 加载联系人映射
     */
    loadContacts() {
        const contactsPath = path.join(__dirname, '..', 'references', 'contacts.json');
        try {
            if (fs.existsSync(contactsPath)) {
                const content = fs.readFileSync(contactsPath, 'utf-8');
                this.contacts = JSON.parse(content);
            }
        }
        catch (e) {
            console.warn('加载联系人失败:', e);
        }
    }
    /**
     * 根据姓名获取用户ID
     */
    getUserIdByName(userName) {
        for (const [userId, info] of Object.entries(this.contacts)) {
            if (typeof info === 'object' && info.name === userName) {
                return userId;
            }
            else if (typeof info === 'string' && info === userName) {
                return userId;
            }
        }
        return null;
    }
    /**
     * 下载图片 - 使用 Resource API（支持下载任何人发的图片）
     * @param messageId 消息ID
     * @param fileKey 文件/图片key
     */
    async downloadImageByResource(messageId, fileKey) {
        if (!this.token) {
            throw new Error('Token not set');
        }
        try {
            // 使用 Resource API 下载图片（支持下载任何人发的图片）
            const url = `${FEISHU_API_BASE}/im/v1/messages/${messageId}/resources/${fileKey}?type=image`;
            const response = await axios_1.default.get(url, {
                headers: { Authorization: `Bearer ${this.token}` },
                responseType: 'arraybuffer',
                timeout: 30000
            });
            if (response.status === 200) {
                console.log(`✅ 通过 Resource API 下载图片成功: ${fileKey}`);
                return Buffer.from(response.data);
            }
            return null;
        }
        catch (e) {
            console.error('通过 Resource API 下载图片失败:', e.message);
            return null;
        }
    }
    /**
     * 下载图片 - 兼容旧版（使用 Images API，只能下载自己发的图片）
     * @deprecated 请使用 downloadImageByResource
     */
    async downloadImage(imageKey) {
        if (!this.token) {
            throw new Error('Token not set');
        }
        try {
            const url = `${FEISHU_API_BASE}/im/v1/images/${imageKey}`;
            const response = await axios_1.default.get(url, {
                headers: { Authorization: `Bearer ${this.token}` },
                responseType: 'arraybuffer',
                timeout: 30000
            });
            if (response.status === 200) {
                return Buffer.from(response.data);
            }
            return null;
        }
        catch (e) {
            console.error('下载图片失败:', e.message);
            return null;
        }
    }
    /**
     * 上传图片到飞书
     */
    async uploadImage(imageBuffer, contentType = 'image/png') {
        if (!this.token) {
            throw new Error('Token not set');
        }
        try {
            const url = `${FEISHU_API_BASE}/im/v1/images`;
            // 构建 multipart/form-data
            const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);
            const formData = this.buildFormData(imageBuffer, boundary, contentType);
            const response = await axios_1.default.post(url, formData, {
                headers: {
                    Authorization: `Bearer ${this.token}`,
                    'Content-Type': `multipart/form-data; boundary=${boundary}`
                },
                timeout: 30000
            });
            if (response.data?.code === 0) {
                return response.data.data?.image_key;
            }
            return null;
        }
        catch (e) {
            console.error('上传图片失败:', e);
            return null;
        }
    }
    /**
     * 构建表单数据
     */
    buildFormData(buffer, boundary, contentType) {
        const prefix = Buffer.from(`--${boundary}\r\n` +
            `Content-Disposition: form-data; name="image_type"\r\n\r\n` +
            `message\r\n` +
            `--${boundary}\r\n` +
            `Content-Disposition: form-data; name="image"; filename="image.${contentType.split('/')[1] || 'png'}"\r\n` +
            `Content-Type: ${contentType}\r\n\r\n`);
        const suffix = Buffer.from(`\r\n--${boundary}--\r\n`);
        return Buffer.concat([prefix, buffer, suffix]);
    }
    /**
     * 转发消息
     */
    async forwardMessage(params) {
        const { sourceChat, reporter, content, messageType, sourceChatId, messageId, imageKey, recordBitable } = params;
        // 获取配置
        const forwardConfig = this.getForwardConfig(sourceChatId);
        if (!forwardConfig) {
            return {
                success: false,
                error: `未找到来源群配置: ${sourceChatId}，请在 config.json 中添加配置`
            };
        }
        const targetChatId = forwardConfig.target_chat_id;
        const handlers = forwardConfig.handlers;
        console.log(`📋 转发配置: ${sourceChat} → ${targetChatId}`);
        console.log(`👥 处理人: ${handlers.map(h => h.user_name).join(', ')}`);
        // 处理图片 - 使用 Resource API 下载（支持任何人发的图片）
        let newImageKey = null;
        if (imageKey) {
            console.log(`📥 尝试下载图片: ${imageKey}`);
            // 使用 Resource API 下载图片（支持下载任何人发的图片）
            let imageBuffer = await this.downloadImageByResource(messageId, imageKey);
            if (!imageBuffer) {
                console.log('❌ 图片下载失败，无法转发');
                return {
                    success: false,
                    error: '图片下载失败，无法转发。请检查消息 ID 和图片 key 是否正确。'
                };
            }
            console.log('📤 上传图片到目标群...');
            newImageKey = await this.uploadImage(imageBuffer);
            if (newImageKey) {
                console.log('✅ 图片转发成功');
            }
            else {
                console.log('❌ 图片上传失败');
                return {
                    success: false,
                    error: '图片上传失败'
                };
            }
        }
        // 构建@列表
        let atList = [...handlers];
        // 需求类额外@Boss
        if (messageType === '需求' && forwardConfig.notify_boss_for_requirement) {
            atList.push({
                user_id: this.config.boss.user_id,
                user_name: this.config.boss.user_name
            });
        }
        // 构建标题
        const title = `【产研反馈-${messageType}】`;
        // 发送消息
        try {
            const result = await this.sendPostMessage({
                chatId: targetChatId,
                title,
                content: `反馈人：${reporter} | 来源：${sourceChat}\n\n问题描述：\n${content}`,
                imageKey: newImageKey,
                atList
            });
            if (result.code !== 0) {
                return {
                    success: false,
                    error: `发送消息失败: ${JSON.stringify(result)}`
                };
            }
            console.log('✅ 已转发到目标群');
            return {
                success: true,
                imageForwarded: newImageKey !== null
            };
        }
        catch (e) {
            return {
                success: false,
                error: `转发失败: ${e.message}`
            };
        }
    }
    /**
     * 验证@人员配置是否有效
     * 确保 user_id 和 user_name 都不为空
     */
    validateAtList(atList) {
        const valid = [];
        const invalid = [];
        for (const at of atList) {
            if (at.user_id && at.user_id.trim() !== '' && at.user_name && at.user_name.trim() !== '') {
                valid.push(at);
            }
            else {
                invalid.push(at);
                console.warn(`⚠️ @高亮格式验证失败: user_id=${at.user_id}, user_name=${at.user_name}`);
            }
        }
        return { valid, invalid };
    }
    /**
     * 发送 Post 消息
     */
    async sendPostMessage(params) {
        if (!this.token) {
            throw new Error('Token not set');
        }
        const { chatId, title, content, imageKey, atList } = params;
        // @格式验证：确保 user_id 和 user_name 都不为空
        const { valid: validAtList, invalid: invalidAtList } = this.validateAtList(atList);
        if (invalidAtList.length > 0) {
            console.warn(`⚠️ 发现 ${invalidAtList.length} 个无效的@配置，已过滤。无效的@将以纯文本形式显示。`);
        }
        // 构造内容块
        const contentBlocks = [];
        // 正文
        contentBlocks.push([{ tag: 'text', text: content }]);
        // 图片
        if (imageKey) {
            contentBlocks.push([{ tag: 'img', image_key: imageKey }]);
        }
        // @人员（只使用验证通过的@列表）
        if (validAtList.length > 0) {
            contentBlocks.push([{ tag: 'text', text: '' }]);
            const atPara = [];
            validAtList.forEach((at, index) => {
                if (index > 0) {
                    atPara.push({ tag: 'text', text: ' ' });
                }
                atPara.push({
                    tag: 'at',
                    user_id: at.user_id,
                    user_name: at.user_name
                });
            });
            atPara.push({ tag: 'text', text: ' 请查看~' });
            contentBlocks.push(atPara);
        }
        // 如果有过滤掉的无效@，以纯文本形式显示
        if (invalidAtList.length > 0) {
            const invalidNames = invalidAtList.map(at => at.user_name || '未知用户').join('、');
            contentBlocks.push([{ tag: 'text', text: '' }]);
            contentBlocks.push([{ tag: 'text', text: `@${invalidNames} 请查看~` }]);
        }
        // 发送
        const url = `${FEISHU_API_BASE}/im/v1/messages?receive_id_type=chat_id`;
        const messageContent = {
            zh_cn: {
                title,
                content: contentBlocks
            }
        };
        const payload = {
            receive_id: chatId,
            msg_type: 'post',
            content: JSON.stringify(messageContent)
        };
        // 调试日志：打印完整的 payload
        console.log('📤 发送消息 Payload:');
        console.log(JSON.stringify(payload, null, 2));
        // 记录请求 payload（发送前）
        const requestLog = {
            url,
            headers: {
                Authorization: `Bearer ${this.token?.substring(0, 10)}...`, // 脱敏显示
                'Content-Type': 'application/json'
            },
            data: payload
        };
        const response = await axios_1.default.post(url, payload, {
            headers: {
                Authorization: `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            timeout: 30000
        });
        // 记录完整报文（发送后）
        this.logForwardPayload(chatId, title, requestLog, response.data);
        return response.data;
    }
    /**
     * 转发回复到来源群
     */
    async forwardReplyToSource(params) {
        const { matchedRecord, status, result, senderName } = params;
        // 从记录中获取来源群和反馈人
        const sourceChatId = matchedRecord.fields['来源群'];
        const feedbackUser = matchedRecord.fields['反馈人'];
        const title = matchedRecord.fields['业务反馈问题记录表'] || '未知问题';
        if (!sourceChatId) {
            console.log('  ⚠️ 未找到来源群信息，跳过转发');
            return false;
        }
        // 构建内容块
        const contentBlocks = [];
        // 标题
        contentBlocks.push([{ tag: 'text', text: '【问题处理结果】', style: { bold: true } }]);
        contentBlocks.push([{ tag: 'text', text: '' }]);
        // 问题信息
        contentBlocks.push([{ tag: 'text', text: `问题：${title}` }]);
        contentBlocks.push([{ tag: 'text', text: `处理人：${senderName}` }]);
        contentBlocks.push([{ tag: 'text', text: `状态：${status}` }]);
        contentBlocks.push([{ tag: 'text', text: `结果：${result}` }]);
        contentBlocks.push([{ tag: 'text', text: '' }]);
        // @反馈人
        if (feedbackUser) {
            const feedbackUserId = this.getUserIdByName(feedbackUser);
            if (feedbackUserId) {
                contentBlocks.push([
                    { tag: 'at', user_id: feedbackUserId, user_name: feedbackUser },
                    { tag: 'text', text: ' 问题已处理，请查看~' }
                ]);
            }
            else {
                contentBlocks.push([{ tag: 'text', text: `@${feedbackUser} 问题已处理，请查看~` }]);
            }
        }
        // 发送消息
        try {
            const url = `${FEISHU_API_BASE}/im/v1/messages?receive_id_type=chat_id`;
            const postContent = {
                zh_cn: {
                    title: '【问题处理结果】',
                    content: contentBlocks
                }
            };
            const payload = {
                receive_id: sourceChatId,
                msg_type: 'post',
                content: JSON.stringify(postContent)
            };
            const response = await axios_1.default.post(url, payload, {
                headers: {
                    Authorization: `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });
            if (response.data?.code === 0) {
                console.log('  ✅ 已转发回复到来源群');
                return true;
            }
            else {
                console.log(`  ⚠️ 转发失败: ${JSON.stringify(response.data)}`);
                return false;
            }
        }
        catch (e) {
            console.log(`  ⚠️ 转发异常: ${e.message}`);
            return false;
        }
    }
    /**
     * 获取转发配置
     */
    getForwardConfig(sourceChatId) {
        const config = this.config.forwardConfigs[sourceChatId];
        if (config) {
            return {
                ...config,
                handlers: config.handlers.filter(h => h.user_id)
            };
        }
        // 未找到配置
        console.error(`未找到来源群配置: ${sourceChatId}`);
        return null;
    }
}
exports.Forwarder = Forwarder;
// 导出
exports.default = Forwarder;
//# sourceMappingURL=forwarder.js.map
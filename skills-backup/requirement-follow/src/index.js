"use strict";
/**
 * Requirement Follow Skill - 完整需求跟进解决方案
 * 版本：3.0.0 - 整合自 requirement_follow.py
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
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RequirementFollowWorkflow = exports.BitableClient = exports.FeishuAPI = void 0;
exports.getDefaultConfig = getDefaultConfig;
exports.startRequirementFollow = startRequirementFollow;
exports.completeRequirementFollow = completeRequirementFollow;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const api_1 = require("./api");
Object.defineProperty(exports, "FeishuAPI", { enumerable: true, get: function () { return api_1.FeishuAPI; } });
const bitable_1 = require("./bitable");
Object.defineProperty(exports, "BitableClient", { enumerable: true, get: function () { return bitable_1.BitableClient; } });
// 重新导出原有模块（保持兼容性）
__exportStar(require("./research"), exports);
// 默认配置
const DEFAULT_REQUIREMENT_TABLE_ID = 'tbl0vJo8gPHIeZ9y';
const DEFAULT_REQUIREMENT_APP_TOKEN = 'Op8WbbFewaq1tasfO8IcQkXmnFf';
const DEFAULT_BOSS_ID = 'ou_3e48baef1bd71cc89fb5a364be55cafc';
const PRD_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'prd');
if (!fs.existsSync(PRD_DIR))
    fs.mkdirSync(PRD_DIR, { recursive: true });
// ==================== 配置加载 ====================
function loadFeishuCreds() {
    try {
        const configPath = path.join(process.env.HOME || '', '.openclaw', 'openclaw.json');
        const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        const feishuConfig = config.channels?.feishu || {};
        if (feishuConfig.appId && feishuConfig.appSecret) {
            return { appId: feishuConfig.appId, appSecret: feishuConfig.appSecret };
        }
    }
    catch (e) {
        console.error('❌ 加载配置失败:', e);
    }
    return null;
}
function getDefaultConfig() {
    const creds = loadFeishuCreds();
    if (!creds)
        return null;
    return {
        appId: creds.appId,
        appSecret: creds.appSecret,
        requirementTableId: process.env.REQUIREMENT_TABLE_ID || DEFAULT_REQUIREMENT_TABLE_ID,
        requirementAppToken: process.env.REQUIREMENT_APP_TOKEN || DEFAULT_REQUIREMENT_APP_TOKEN,
        bossId: process.env.BOSS_ID || DEFAULT_BOSS_ID
    };
}
// ==================== 工作流类 ====================
class RequirementFollowWorkflow {
    constructor(config) {
        this.config = config;
        this.api = new api_1.FeishuAPI({ appId: config.appId, appSecret: config.appSecret });
        this.bitable = new bitable_1.BitableClient({
            appToken: config.requirementAppToken,
            tableId: config.requirementTableId,
            feishuApi: this.api
        });
    }
    async startWorkflow(params) {
        console.log('='.repeat(60));
        console.log('🚀 启动需求跟进流程');
        console.log('='.repeat(60));
        console.log(`📨 需求内容: ${params.requirementContent.slice(0, 50)}...`);
        console.log(`👤 需求方: ${params.requesterName}`);
        // 检查重复需求
        const similar = await this.bitable.findSimilarRequirement(params.requirementContent);
        if (similar) {
            return {
                success: true,
                isDuplicate: true,
                existingRecordId: similar.record_id,
                error: `发现相似需求 (相似度: ${(similar.similarity * 100).toFixed(0)}%)`
            };
        }
        // 创建需求记录
        const recordId = await this.bitable.createRecord({
            requirementContent: params.requirementContent,
            requesterName: params.requesterName,
            requesterId: params.requesterId,
            sourceChatId: params.sourceChatId,
            sourceChatName: params.sourceChatName,
            originalMessageId: params.originalMessageId
        });
        if (!recordId)
            return { success: false, error: '创建需求记录失败' };
        // 准备成员列表
        const membersToAdd = [params.requesterId, this.config.bossId];
        if (params.additionalMembers)
            membersToAdd.push(...params.additionalMembers);
        const uniqueMembers = [...new Set(membersToAdd.filter(id => id))];
        // 创建调研群
        const chatInfo = await this.createResearchChatWithRetry({
            requirementId: recordId,
            requirementContent: params.requirementContent,
            requesterName: params.requesterName,
            members: uniqueMembers
        });
        if (!chatInfo) {
            await this.bitable.updateRecord(recordId, { 需求状态: '创建失败', 调研群名称: '群创建失败' });
            return { success: false, error: '创建调研群失败', recordId };
        }
        // 验证群成员
        const validation = await this.api.validateChatMembers(chatInfo.chat_id, uniqueMembers);
        if (!validation.valid && validation.disbanded) {
            await this.bitable.updateRecord(recordId, { 需求状态: '创建失败', 调研群名称: '群成员验证失败' });
            return { success: false, error: '群成员验证失败', recordId };
        }
        // 更新记录关联调研群
        await this.bitable.updateResearchChat(recordId, chatInfo.chat_id, chatInfo.name);
        // 添加成员
        await this.addMembersWithFallback(chatInfo.chat_id, uniqueMembers, {
            [params.requesterId]: params.requesterName,
            [this.config.bossId]: 'Boss'
        }, chatInfo.name);
        // 发送欢迎消息
        await this.api.sendWelcomeMessage(chatInfo.chat_id, params.requirementContent, params.requesterName, params.requesterId);
        console.log('✅ 需求跟进流程启动完成');
        return { success: true, recordId, chatId: chatInfo.chat_id, chatName: chatInfo.name };
    }
    async createResearchChatWithRetry(params) {
        const { requirementId, requirementContent, requesterName, members, maxRetries = 2 } = params;
        const today = new Date().toISOString().slice(5, 10).replace('-', '');
        const chatName = `需求调研-${requesterName}-${today}`;
        const description = `需求调研群\n需求记录: ${requirementId}\n摘要: ${requirementContent.slice(0, 30)}...`;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                if (attempt > 1)
                    await new Promise(r => setTimeout(r, attempt * 3000));
                const chatInfo = await this.api.createChat({ name: chatName, description, chat_mode: 'group', chat_type: 'private', user_id_list: members });
                await new Promise(r => setTimeout(r, 3000));
                const validation = await this.api.validateChatMembers(chatInfo.chat_id, members);
                if (validation.valid)
                    return chatInfo;
                if (validation.disbanded)
                    continue;
                return chatInfo;
            }
            catch (e) {
                console.error(`第${attempt}次创建群失败:`, e);
            }
        }
        return null;
    }
    async addMembersWithFallback(chatId, userIds, userNames, chatName) {
        await new Promise(r => setTimeout(r, 5000));
        let result = await this.api.addMembersToChat(chatId, userIds);
        if (result.failed.length > 0) {
            await new Promise(r => setTimeout(r, 3000));
            const failedIds = result.failed.map(f => f.user_id);
            const retryResult = await this.api.addMembersToChat(chatId, failedIds);
            result.failed = retryResult.failed;
            result.added.push(...retryResult.added);
        }
        // 发送私信邀请
        for (const failed of result.failed) {
            await this.api.sendChatInvite(failed.user_id, chatId, chatName, { userName: userNames[failed.user_id] });
        }
    }
    async completeWorkflow(requirementId, chatContext = '') {
        const record = await this.bitable.getRecord(requirementId);
        if (!record)
            return { success: false, error: '获取需求记录失败' };
        const fields = record.fields || record;
        const chatId = fields.调研群ID;
        // 生成 PRD
        const prdPath = await this.generatePRD({
            requirementId,
            requirementContent: fields.需求内容 || '',
            requester: fields.需求方 || 'Unknown',
            chatContext
        });
        if (!prdPath)
            return { success: false, error: '生成 PRD 失败' };
        await this.bitable.updateStatus(requirementId, '已完成', prdPath);
        let chatDisbanded = false;
        if (chatId) {
            await this.api.sendDisbandNotice(chatId);
            await new Promise(r => setTimeout(r, 3000));
            chatDisbanded = await this.api.disbandChat(chatId);
        }
        return { success: true, requirementId, prdPath, chatDisbanded };
    }
    async generatePRD(params) {
        const today = new Date().toISOString().split('T')[0];
        const prdPath = path.join(PRD_DIR, `prd-${params.requirementId}-${Date.now()}.md`);
        const content = `# PRD文档\n\n**需求ID**: ${params.requirementId}\n**需求方**: ${params.requester}\n**生成日期**: ${today}\n\n## 需求描述\n${params.requirementContent}\n\n## 调研记录\n${params.chatContext}\n`;
        try {
            fs.writeFileSync(prdPath, content, 'utf-8');
            console.log(`✅ PRD 文档已生成: ${prdPath}`);
            return prdPath;
        }
        catch (e) {
            console.error('生成 PRD 失败:', e);
            return null;
        }
    }
    getApi() { return this.api; }
    getBitable() { return this.bitable; }
}
exports.RequirementFollowWorkflow = RequirementFollowWorkflow;
// ==================== 便捷函数 ====================
async function startRequirementFollow(params) {
    const config = params.config || getDefaultConfig();
    if (!config)
        return { success: false, error: '无法加载飞书配置' };
    const workflow = new RequirementFollowWorkflow(config);
    return workflow.startWorkflow(params);
}
async function completeRequirementFollow(requirementId, chatContext, config) {
    const cfg = config || getDefaultConfig();
    if (!cfg)
        return { success: false, error: '无法加载飞书配置' };
    const workflow = new RequirementFollowWorkflow(cfg);
    return workflow.completeWorkflow(requirementId, chatContext);
}
exports.default = RequirementFollowWorkflow;
//# sourceMappingURL=index.js.map
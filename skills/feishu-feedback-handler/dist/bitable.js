"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BitableClient = void 0;
const utils_1 = require("./utils");
class BitableClient {
    constructor(config) {
        this.token = null;
        this.config = config;
        // 兼容处理
        if (!this.config.appToken && this.config.app_token) {
            this.config.appToken = this.config.app_token;
        }
        if (!this.config.tableId && this.config.table_id) {
            this.config.tableId = this.config.table_id;
        }
    }
    async init() {
        this.token = await (0, utils_1.getTenantAccessToken)();
    }
    /**
     * 设置 token
     */
    setToken(token) {
        this.token = token;
    }
    /**
     * 创建新记录
     */
    async createRecord(data) {
        if (!this.token)
            await this.init();
        const fields = {
            '业务反馈问题记录表': data.title,
            '反馈时间': data.feedbackTime,
            '反馈人': data.feedbackUser,
            '反馈来源': data.feedbackSource,
            '问题内容': data.content,
            '来源群': data.sourceChatId,
            '类型': data.type,
            '处理状态': '待处理'
        };
        if (data.originalMessageId) {
            fields['原始消息ID'] = data.originalMessageId;
        }
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ fields })
            });
            const result = await response.json();
            if (result.code === 0) {
                console.log('✅ 记录创建成功:', result.data?.record?.record_id);
                return result.data?.record?.record_id || null;
            }
            else {
                console.error('❌ 创建记录失败:', result);
                return null;
            }
        }
        catch (error) {
            console.error('❌ 创建记录异常:', error);
            return null;
        }
    }
    /**
     * 创建需求跟进记录（写入需求跟进清单表）
     */
    async createRequirementRecord(data) {
        if (!this.token)
            await this.init();
        // 需求跟进清单表的配置
        const REQUIREMENT_APP_TOKEN = 'Op8WbbFewaq1tasfO8IcQkXmnFf';
        const REQUIREMENT_TABLE_ID = 'tbl0vJo8gPHIeZ9y';
        const timestampMs = Date.now();
        const fields = {
            '需求内容': data.requirementContent,
            '需求状态': '待跟进',
            '需求时间': timestampMs,
            '来源群': data.sourceChatName,
            '来源群ID': data.sourceChatId,
            '需求方': data.requesterName,
            '需求方ID': data.requesterId,
            '调研群ID': data.researchChatId,
            '调研群名称': data.researchChatName,
            '原始消息ID': data.originalMessageId,
            '需求跟进清单': `需求: ${data.requirementContent.slice(0, 30)}...`
        };
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${REQUIREMENT_APP_TOKEN}/tables/${REQUIREMENT_TABLE_ID}/records`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ fields })
            });
            const result = await response.json();
            if (result.code === 0) {
                console.log('✅ 需求跟进记录创建成功:', result.data?.record?.record_id);
                return result.data?.record?.record_id || null;
            }
            else {
                console.error('❌ 创建需求跟进记录失败:', result);
                return null;
            }
        }
        catch (error) {
            console.error('❌ 创建需求跟进记录异常:', error);
            return null;
        }
    }
    /**
     * 更新记录状态
     */
    async updateStatus(recordId, status, result) {
        if (!this.token)
            await this.init();
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records/${recordId}`;
        const payload = {
            fields: {
                '处理状态': status,
                '处理结果': result
            }
        };
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (data.code === 0) {
                console.log('✅ 状态更新成功');
                return true;
            }
            else {
                console.error('❌ 更新状态失败:', data);
                return false;
            }
        }
        catch (error) {
            console.error('❌ 更新状态异常:', error);
            return false;
        }
    }
    /**
     * 根据关键词搜索记录
     */
    async searchByKeywords(keywords) {
        if (!this.token)
            await this.init();
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records?page_size=100`;
        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            const result = await response.json();
            if (result.code !== 0)
                return null;
            const records = result.data?.items || [];
            for (const keyword of keywords) {
                for (const record of records) {
                    const fields = record.fields || {};
                    const status = fields['处理状态'] || '';
                    // 跳过已解决/已关闭的
                    if (status === '已解决' || status === '已关闭')
                        continue;
                    const title = fields['业务反馈问题记录表'] || '';
                    const content = fields['问题内容'] || '';
                    if (title.includes(keyword) || content.includes(keyword)) {
                        return {
                            record_id: record.record_id,
                            title,
                            content,
                            status,
                            来源群: fields['来源群'],
                            反馈人: fields['反馈人'],
                            原始消息ID: fields['原始消息ID']
                        };
                    }
                }
            }
            return null;
        }
        catch (error) {
            console.error('搜索记录失败:', error);
            return null;
        }
    }
    /**
     * 添加字段选项（反馈来源字段）
     */
    async addFieldOption(fieldId, optionName) {
        if (!this.token)
            await this.init();
        // 注意：飞书API不支持直接添加选项，这里记录需要手动添加
        console.log(`⚠️ 需要手动添加选项 "${optionName}" 到反馈来源字段`);
        return true;
    }
    /**
     * 根据关键词搜索记录（兼容方法）
     */
    async findRecordByKeywords(keywords) {
        return this.searchByKeywords(keywords);
    }
    /**
     * 更新记录状态（兼容方法）
     */
    async updateRecordStatus(recordId, status, result) {
        return this.updateStatus(recordId, status, result);
    }
}
exports.BitableClient = BitableClient;
//# sourceMappingURL=bitable.js.map
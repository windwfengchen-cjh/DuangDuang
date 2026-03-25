"use strict";
/**
 * Bitable 多维表格 API 封装
 * 用于需求跟进清单表的 CRUD 操作
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.BitableClient = void 0;
/**
 * Bitable 客户端
 */
class BitableClient {
    constructor(config) {
        this.config = config;
    }
    /**
     * 获取 API 请求头
     */
    async getHeaders() {
        const token = await this.config.feishuApi.getTenantAccessToken();
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    /**
     * 创建需求记录
     */
    async createRecord(params) {
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records`;
        const timestamp = Date.now();
        const fields = {
            '需求内容': params.requirementContent,
            '需求状态': '待跟进',
            '需求时间': timestamp,
            '来源群': params.sourceChatName,
            '需求方': params.requesterName,
            '需求方ID': params.requesterId,
            '来源群ID': params.sourceChatId,
            '原始消息ID': params.originalMessageId || '',
            '需求跟进清单': `需求: ${params.requirementContent.slice(0, 30)}...`
        };
        if (params.researchChatId) {
            fields['调研群ID'] = params.researchChatId;
        }
        if (params.researchChatName) {
            fields['调研群名称'] = params.researchChatName;
        }
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: await this.getHeaders(),
                body: JSON.stringify({ fields })
            });
            const data = await response.json();
            if (data.code === 0 && data.data) {
                console.log(`✅ 需求记录创建成功: ${data.data.record.record_id}`);
                return data.data.record.record_id;
            }
            else {
                console.error(`❌ 创建记录失败:`, data);
                return null;
            }
        }
        catch (e) {
            console.error(`❌ 创建记录异常:`, e);
            return null;
        }
    }
    /**
     * 更新需求记录
     */
    async updateRecord(recordId, fields) {
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records/${recordId}`;
        // 转换字段名
        const apiFields = {};
        if (fields.需求内容 !== undefined)
            apiFields['需求内容'] = fields.需求内容;
        if (fields.需求状态 !== undefined)
            apiFields['需求状态'] = fields.需求状态;
        if (fields.需求时间 !== undefined)
            apiFields['需求时间'] = fields.需求时间;
        if (fields.来源群 !== undefined)
            apiFields['来源群'] = fields.来源群;
        if (fields.需求方 !== undefined)
            apiFields['需求方'] = fields.需求方;
        if (fields.需求方ID !== undefined)
            apiFields['需求方ID'] = fields.需求方ID;
        if (fields.来源群ID !== undefined)
            apiFields['来源群ID'] = fields.来源群ID;
        if (fields.原始消息ID !== undefined)
            apiFields['原始消息ID'] = fields.原始消息ID;
        if (fields.调研群ID !== undefined)
            apiFields['调研群ID'] = fields.调研群ID;
        if (fields.调研群名称 !== undefined)
            apiFields['调研群名称'] = fields.调研群名称;
        if (fields.PRD文档链接 !== undefined)
            apiFields['PRD文档链接'] = fields.PRD文档链接;
        if (fields.需求跟进清单 !== undefined)
            apiFields['需求跟进清单'] = fields.需求跟进清单;
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: await this.getHeaders(),
                body: JSON.stringify({ fields: apiFields })
            });
            const data = await response.json();
            if (data.code === 0) {
                console.log(`✅ 需求记录更新成功: ${recordId}`);
                return true;
            }
            else {
                console.error(`❌ 更新记录失败:`, data);
                return false;
            }
        }
        catch (e) {
            console.error(`❌ 更新记录异常:`, e);
            return false;
        }
    }
    /**
     * 获取需求记录
     */
    async getRecord(recordId) {
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records/${recordId}`;
        try {
            const response = await fetch(url, { headers: await this.getHeaders() });
            const data = await response.json();
            if (data.code === 0 && data.data) {
                return data.data.record;
            }
            return null;
        }
        catch (e) {
            console.error(`❌ 获取记录失败:`, e);
            return null;
        }
    }
    /**
     * 查询相似需求（基于关键词匹配）
     */
    async findSimilarRequirement(content, threshold = 0.85) {
        const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${this.config.appToken}/tables/${this.config.tableId}/records?page_size=100`;
        try {
            const response = await fetch(url, { headers: await this.getHeaders() });
            const data = await response.json();
            if (data.code !== 0 || !data.data)
                return null;
            const keywords = this.extractKeywords(content);
            for (const item of data.data.items) {
                const existingContent = item.fields.需求内容 || '';
                if (!existingContent)
                    continue;
                const similarity = this.calculateSimilarity(keywords, this.extractKeywords(existingContent));
                if (similarity >= threshold) {
                    console.log(`✅ 发现相似需求: ${item.record_id} (相似度 ${(similarity * 100).toFixed(0)}%)`);
                    return { record_id: item.record_id, similarity };
                }
            }
            return null;
        }
        catch (e) {
            console.error(`⚠️ 查找相似需求出错:`, e);
            return null;
        }
    }
    /**
     * 提取关键词
     */
    extractKeywords(text) {
        const cleaned = text.toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, ' ');
        return new Set(cleaned.split(/\s+/).filter(w => w.length > 1));
    }
    /**
     * 计算相似度
     */
    calculateSimilarity(words1, words2) {
        if (words1.size === 0 || words2.size === 0)
            return 0;
        const intersection = new Set([...words1].filter(x => words2.has(x)));
        const union = new Set([...words1, ...words2]);
        return intersection.size / union.size;
    }
    /**
     * 更新需求状态
     */
    async updateStatus(recordId, status, prdLink) {
        const fields = { 需求状态: status };
        if (prdLink) {
            fields.PRD文档链接 = { text: 'PRD文档', link: prdLink };
        }
        return this.updateRecord(recordId, fields);
    }
    /**
     * 更新调研群信息
     */
    async updateResearchChat(recordId, chatId, chatName) {
        return this.updateRecord(recordId, {
            需求状态: '跟进中',
            调研群ID: chatId,
            调研群名称: chatName
        });
    }
}
exports.BitableClient = BitableClient;
exports.default = BitableClient;
;
//# sourceMappingURL=bitable.js.map
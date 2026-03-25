/**
 * Bitable 多维表格 API 封装
 * 用于需求跟进清单表的 CRUD 操作
 */
import { FeishuAPI } from './api';
export interface RequirementFields {
    需求内容?: string;
    需求状态?: '待跟进' | '跟进中' | '已完成' | '已取消' | '创建失败';
    需求时间?: number;
    来源群?: string;
    需求方?: string;
    需求方ID?: string;
    来源群ID?: string;
    原始消息ID?: string;
    调研群ID?: string;
    调研群名称?: string;
    PRD文档链接?: {
        text: string;
        link: string;
    } | string;
    需求跟进清单?: string;
}
export interface RequirementRecord {
    record_id: string;
    fields: RequirementFields;
}
export interface CreateRequirementParams {
    requirementContent: string;
    requesterName: string;
    requesterId: string;
    sourceChatId: string;
    sourceChatName: string;
    researchChatId?: string;
    researchChatName?: string;
    originalMessageId?: string;
}
export interface BitableConfig {
    appToken: string;
    tableId: string;
    feishuApi: FeishuAPI;
}
/**
 * Bitable 客户端
 */
export declare class BitableClient {
    private config;
    constructor(config: BitableConfig);
    /**
     * 获取 API 请求头
     */
    private getHeaders;
    /**
     * 创建需求记录
     */
    createRecord(params: CreateRequirementParams): Promise<string | null>;
    /**
     * 更新需求记录
     */
    updateRecord(recordId: string, fields: Partial<RequirementFields>): Promise<boolean>;
    /**
     * 获取需求记录
     */
    getRecord(recordId: string): Promise<RequirementRecord | null>;
    /**
     * 查询相似需求（基于关键词匹配）
     */
    findSimilarRequirement(content: string, threshold?: number): Promise<{
        record_id: string;
        similarity: number;
    } | null>;
    /**
     * 提取关键词
     */
    private extractKeywords;
    /**
     * 计算相似度
     */
    private calculateSimilarity;
    /**
     * 更新需求状态
     */
    updateStatus(recordId: string, status: RequirementFields['需求状态'], prdLink?: string): Promise<boolean>;
    /**
     * 更新调研群信息
     */
    updateResearchChat(recordId: string, chatId: string, chatName: string): Promise<boolean>;
}
export default BitableClient;
//# sourceMappingURL=bitable.d.ts.map
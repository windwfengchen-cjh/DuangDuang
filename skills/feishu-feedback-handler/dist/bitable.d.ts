export interface BitableConfig {
    app_token: string;
    table_id: string;
    appToken?: string;
    tableId?: string;
}
export interface RecordData {
    title: string;
    feedbackTime: number;
    feedbackUser: string;
    feedbackSource: string;
    content: string;
    sourceChatId: string;
    type: '问题' | '需求' | '咨询';
    originalMessageId?: string;
}
export declare class BitableClient {
    private config;
    private token;
    constructor(config: BitableConfig);
    init(): Promise<void>;
    /**
     * 设置 token
     */
    setToken(token: string): void;
    /**
     * 创建新记录
     */
    createRecord(data: RecordData): Promise<string | null>;
    /**
     * 更新记录状态
     */
    updateStatus(recordId: string, status: string, result: string): Promise<boolean>;
    /**
     * 根据关键词搜索记录
     */
    searchByKeywords(keywords: string[]): Promise<any | null>;
    /**
     * 添加字段选项（反馈来源字段）
     */
    addFieldOption(fieldId: string, optionName: string): Promise<boolean>;
    /**
     * 根据关键词搜索记录（兼容方法）
     */
    findRecordByKeywords(keywords: string[]): Promise<any | null>;
    /**
     * 更新记录状态（兼容方法）
     */
    updateRecordStatus(recordId: string, status: string, result: string): Promise<boolean>;
}
//# sourceMappingURL=bitable.d.ts.map
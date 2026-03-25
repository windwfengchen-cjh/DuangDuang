/**
 * 从 OpenClaw 配置加载飞书凭证
 */
export declare function loadFeishuCreds(): Promise<{
    appId: string | null;
    appSecret: string | null;
}>;
/**
 * 获取飞书 tenant_access_token
 */
export declare function getTenantAccessToken(): Promise<string>;
/**
 * 从 contacts.json 查找用户 Open ID
 */
export declare function getUserIdByName(userName: string): string | null;
/**
 * 构建飞书 @ 标签
 */
export declare function buildAtTag(userName: string): any;
/**
 * 检查消息是否 @ 我
 */
export declare function isAtMe(messageText: string, botId: string): boolean;
/**
 * 移除消息中的 @ 标签
 */
export declare function removeAtTags(messageText: string): string;
/**
 * 提取状态和处理结果
 */
export declare function extractStatusAndResult(messageText: string): {
    status: string | null;
    result: string;
};
/**
 * 提取问题关键词
 */
export declare function extractIssueKeywords(messageText: string): string[];
/**
 * 延迟函数
 */
export declare function delay(ms: number): Promise<void>;
/**
 * 格式化日期
 */
export declare function formatDate(timestamp: number): string;
/**
 * 发送飞书文本消息
 */
export declare function sendFeishuMessage(chatId: string, message: string, token: string): Promise<boolean>;
/**
 * 发送飞书富文本消息（Post类型）
 */
export declare function sendFeishuPostMessage(chatId: string, title: string, content: any[], token: string): Promise<boolean>;
//# sourceMappingURL=utils.d.ts.map
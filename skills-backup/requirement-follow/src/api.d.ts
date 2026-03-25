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
    failed: Array<{
        user_id: string;
        error_code?: number;
        error_msg?: string;
    }>;
    results: AddMemberResult[];
}
export interface MemberValidationResult {
    valid: boolean;
    member_count: number;
    expected_count: number;
    disbanded: boolean;
    error?: string;
}
export declare class FeishuAPI {
    private config;
    private token;
    private tokenExpiry;
    constructor(config: FeishuConfig);
    getTenantAccessToken(): Promise<string>;
    getCurrentToken(): string | null;
    private getHeaders;
    createChat(params: {
        name: string;
        description?: string;
        chat_mode?: 'group' | 'p2p';
        chat_type?: 'public' | 'private';
        user_id_list?: string[];
    }): Promise<ChatInfo>;
    getChatInfo(chatId: string): Promise<ChatInfo | null>;
    disbandChat(chatId: string): Promise<boolean>;
    getChatMembers(chatId: string): Promise<Set<string>>;
    addSingleMember(chatId: string, userId: string, maxRetries?: number): Promise<AddMemberResult>;
    addMembersToChat(chatId: string, userIds: string[], options?: {
        skipExisting?: boolean;
        delayMs?: number;
    }): Promise<AddMembersSummary>;
    validateChatMembers(chatId: string, expectedUserIds: string[], options?: {
        autoDisbandOnEmpty?: boolean;
    }): Promise<MemberValidationResult>;
    sendTextMessage(receiveId: string, text: string, options?: {
        receiveIdType?: 'chat_id' | 'open_id';
    }): Promise<boolean>;
    sendPostMessage(receiveId: string, postContent: {
        title: string;
        content: Array<Array<{
            tag: string;
            text?: string;
            user_id?: string;
            user_name?: string;
            href?: string;
        }>>;
    }, options?: {
        receiveIdType?: 'chat_id' | 'open_id';
    }): Promise<boolean>;
    sendWelcomeMessage(chatId: string, requirementContent: string, requesterName: string, requesterId: string): Promise<boolean>;
    sendDisbandNotice(chatId: string): Promise<boolean>;
    sendChatInvite(userId: string, chatId: string, chatName: string, options?: {
        userName?: string;
    }): Promise<boolean>;
}
export default FeishuAPI;
//# sourceMappingURL=api.d.ts.map
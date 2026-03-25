/**
 * 调研群消息处理模块
 */
export interface FeishuMessageEvent {
    message_id: string;
    chat_id: string;
    chat_type: 'group' | 'p2p';
    sender: {
        sender_id: {
            open_id: string;
        };
        sender_type: string;
        sender_name?: string;
    };
    message_type: string;
    content: string;
    mentions?: Array<{
        key: string;
        id: {
            open_id: string;
        };
        name: string;
    }>;
    create_time: string;
    update_time: string;
}
export interface ChatMessage {
    message_id: string;
    sender_id: string;
    sender_name: string;
    content: string;
    message_type: string;
    create_time: string;
    is_requirement_person: boolean;
}
export type ResearchMode = 'auto_collect' | 'qa' | 'hybrid';
export interface ResearchSession {
    chat_id: string;
    requirement_title: string;
    requirement_person_id: string;
    requirement_person_name: string;
    boss_id: string;
    record_id?: string;
    current_question_idx: number;
    collected_data: Record<string, string>;
    attachments: string[];
    status: 'waiting' | 'collecting' | 'completed' | 'cancelled';
    created_at: string;
    updated_at: string;
    last_message_time?: string;
    message_count: number;
    mode: ResearchMode;
    auto_collect_mode: boolean;
    enable_qa: boolean;
    enable_auto_collect: boolean;
    waiting_for_answer?: boolean;
    auto_collect_deadline?: string;
    processed_message_ids: string[];
}
export declare const RESEARCH_QUESTIONS: {
    key: string;
    question: string;
    required: boolean;
    prd_section: string;
}[];
export declare function formatQuestion(template: string, title: string, requester: string): string;
export declare function loadResearchSession(chatId: string): ResearchSession | null;
export declare function saveResearchSession(session: ResearchSession): void;
export declare function deleteResearchSession(chatId: string): void;
export declare function loadChatMessages(chatId: string): ChatMessage[];
export declare function saveChatMessages(chatId: string, messages: ChatMessage[]): void;
export declare function addChatMessage(chatId: string, message: ChatMessage): void;
export declare function isResearchChat(chatId: string): boolean;
export declare function isAutoCollectExpired(session: ResearchSession): boolean;
export declare function createResearchSession(chatId: string, title: string, personId: string, personName: string, bossId: string, recordId?: string, mode?: ResearchMode, hours?: number): ResearchSession;
export declare function startResearch(chatId: string, token: string): Promise<boolean>;
export declare function handleResearchMessage(event: FeishuMessageEvent, token: string): Promise<{
    handled: boolean;
    result?: any;
}>;
export declare function getResearchStats(chatId: string): {
    messageCount: number;
    status: string;
} | null;
export declare class ResearchHandler {
    private token;
    constructor(token: string);
    handleMessage(event: FeishuMessageEvent): Promise<{
        handled: boolean;
        result?: any;
    }>;
    isResearchChat(chatId: string): boolean;
    getStats(chatId: string): {
        messageCount: number;
        status: string;
    } | null;
}
export default ResearchHandler;
//# sourceMappingURL=research.d.ts.map
/**
 * 需求调研群消息处理器
 * 支持三种模式：
 * 1. 自动收集模式 - 收集群内所有消息（无需@）
 * 2. 问答模式 - 通过7个问题引导需求人回答
 * 3. 混合模式 - 问答+自动收集同时进行（推荐）
 *
 * 混合模式工作流程：
 * 1. 机器人发送7个问题引导需求人
 * 2. 同时自动收集群内所有成员的消息
 * 3. 识别需求人回答后自动发送下一个问题
 * 4. 所有消息（包括讨论）都保存到PRD
 */
import { FeishuMessageEvent } from './index';
/**
 * 调研问题定义 - 7个关键问题模板
 * 混合模式：问题用于引导需求人，同时收集所有群内消息
 */
export declare const RESEARCH_QUESTIONS: {
    key: string;
    question: string;
    required: boolean;
    prd_section: string;
}[];
/**
 * 获取格式化的问题文本（替换变量）
 */
export declare function formatQuestion(questionTemplate: string, title: string, requesterName: string): string;
/**
 * 群消息结构
 */
export interface ChatMessage {
    message_id: string;
    sender_id: string;
    sender_name: string;
    content: string;
    message_type: string;
    create_time: string;
    is_requirement_person: boolean;
}
/**
 * 调研群配置
 */
export interface ResearchChatConfig {
    chat_id: string;
    requirement_title: string;
    requirement_person_id: string;
    requirement_person_name: string;
    boss_id: string;
    record_id?: string;
    created_at: string;
}
/**
 * 调研模式类型
 */
export type ResearchMode = 'auto_collect' | 'qa' | 'hybrid';
/**
 * 调研会话状态
 *
 * 混合模式（hybrid）说明：
 * - 同时启用问答引导和自动收集
 * - 机器人发送7个问题引导需求人
 * - 同时收集群内所有成员的消息和讨论
 * - 识别需求人回答后自动进入下一题
 * - 所有消息都保存到PRD文档
 */
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
    status: 'waiting' | 'collecting' | 'completed' | 'cancelled' | 'auto_collected';
    created_at: string;
    updated_at: string;
    last_message_time?: string;
    message_count: number;
    mode: ResearchMode;
    auto_collect_mode: boolean;
    enable_qa: boolean;
    enable_auto_collect: boolean;
    waiting_for_answer: boolean;
    auto_collect_deadline?: string;
    processed_message_ids: string[];
}
/**
 * 加载调研会话状态
 */
export declare function loadResearchSession(chatId: string): ResearchSession | null;
/**
 * 保存调研会话状态
 */
export declare function saveResearchSession(session: ResearchSession): void;
/**
 * 删除调研会话状态
 */
export declare function deleteResearchSession(chatId: string): void;
/**
 * 加载群消息记录
 */
export declare function loadChatMessages(chatId: string): ChatMessage[];
/**
 * 保存群消息记录
 */
export declare function saveChatMessages(chatId: string, messages: ChatMessage[]): void;
/**
 * 添加消息到记录
 */
export declare function addChatMessage(chatId: string, message: ChatMessage): void;
/**
 * 创建新的调研会话
 *
 * @param mode 调研模式: 'auto_collect' | 'qa' | 'hybrid' (默认hybrid)
 * @param autoCollectHours 自动收集时长（小时）
 */
export declare function createResearchSession(chatId: string, requirementTitle: string, requirementPersonId: string, requirementPersonName: string, bossId: string, recordId?: string, mode?: ResearchMode, // 默认使用混合模式
autoCollectHours?: number): ResearchSession;
/**
 * 检查是否是调研群
 */
export declare function isResearchChat(chatId: string): boolean;
/**
 * 检查是否超出自动收集时间
 */
export declare function isAutoCollectExpired(session: ResearchSession): boolean;
/**
 * 启动调研（发送欢迎消息）
 */
export declare function startResearch(chatId: string, token: string): Promise<boolean>;
/**
 * 处理调研群消息 - 收集所有消息（无需@）
 */
export declare function handleResearchMessage(event: FeishuMessageEvent, token: string): Promise<{
    handled: boolean;
    result?: any;
}>;
/**
 * 获取调研统计信息
 */
export declare function getResearchStats(chatId: string): {
    messageCount: number;
    status: string;
} | null;
//# sourceMappingURL=research.d.ts.map
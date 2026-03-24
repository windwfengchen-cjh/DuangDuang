/**
 * 飞书反馈处理 Skill - 主入口
 * 接收飞书事件，调用转发/更新功能
 */
/**
 * 处理飞书消息事件
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
        sender_email?: string;
    };
    message_type: 'text' | 'post' | 'image' | 'file' | 'audio' | 'media' | 'sticker';
    content: string;
    mentions?: Array<{
        key: string;
        id: {
            open_id: string;
        };
        name: string;
        tenant_key: string;
    }>;
    create_time: string;
    update_time: string;
}
/**
 * 主处理器类
 */
export declare class FeedbackHandler {
    private config;
    private forwarder;
    private bitable;
    private token;
    private tokenExpiry;
    constructor();
    /**
     * 获取有效的 tenant_access_token
     */
    private getToken;
    /**
     * 检查消息是否@了机器人
     */
    private isAtMe;
    /**
     * 处理消息事件
     */
    handleMessage(event: FeishuMessageEvent): Promise<any>;
    /**
     * 判断是否是跟进指令（排除需求跟进）
     */
    private isFollowUpCommand;
    /**
     * 处理需求跟进指令
     * 创建调研群并开始收集需求信息
     */
    private handleRequirementFollow;
    /**
     * 创建调研群
     */
    private createResearchChat;
    /**
     * 发送调研群邀请给Boss
     */
    private sendResearchGroupInvite;
    /**
     * 处理跟进指令
     */
    private handleFollowUp;
    /**
     * 处理功能咨询
     */
    private handleConsultation;
    /**
     * 处理问题/需求反馈
     */
    private handleFeedback;
    /**
     * 提取关键词
     */
    private extractKeywords;
    /**
     * 处理状态更新（来自目标群的回复）
     */
    handleStatusUpdate(event: FeishuMessageEvent): Promise<any>;
    /**
     * 从消息中提取状态和处理结果
     */
    private extractStatusAndResult;
}
export default FeedbackHandler;
//# sourceMappingURL=index.d.ts.map
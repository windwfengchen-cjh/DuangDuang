/**
 * 飞书反馈处理 Skill - 简化版 v3.1
 * 需求跟进逻辑直接调用 requirement-follow skill
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
    message_type: string;
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
    root_id?: string;
    parent_id?: string;
}
export declare class FeedbackHandler {
    private config;
    private forwarder;
    private bitable;
    private token;
    private tokenExpiry;
    constructor();
    private getToken;
    private isAtMe;
    handleMessage(event: FeishuMessageEvent): Promise<any>;
    private isFollowUpCommand;
    /**
     * 处理需求跟进指令 - 直接调用 requirement-follow workflow
     */
    private handleRequirementFollow;
    private handleFollowUp;
    private handleConsultation;
    private handleFeedback;
    private extractKeywords;
    handleStatusUpdate(event: FeishuMessageEvent): Promise<any>;
    private extractStatusAndResult;
}
export default FeedbackHandler;
//# sourceMappingURL=index.d.ts.map
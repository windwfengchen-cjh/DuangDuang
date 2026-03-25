/**
 * Requirement Follow Skill - 完整需求跟进解决方案
 * 版本：3.0.0 - 整合自 requirement_follow.py
 */
import { FeishuAPI } from './api';
import { BitableClient } from './bitable';
export * from './research';
export { FeishuAPI, BitableClient };
export interface RequirementFollowConfig {
    appId: string;
    appSecret: string;
    requirementTableId: string;
    requirementAppToken: string;
    bossId: string;
}
export interface StartWorkflowResult {
    success: boolean;
    isDuplicate?: boolean;
    recordId?: string;
    chatId?: string;
    chatName?: string;
    error?: string;
    existingRecordId?: string;
}
export interface CompleteWorkflowResult {
    success: boolean;
    requirementId?: string;
    prdPath?: string;
    chatDisbanded?: boolean;
    error?: string;
}
export declare function getDefaultConfig(): RequirementFollowConfig | null;
export declare class RequirementFollowWorkflow {
    private api;
    private bitable;
    private config;
    constructor(config: RequirementFollowConfig);
    startWorkflow(params: {
        requirementContent: string;
        requesterName: string;
        requesterId: string;
        sourceChatId: string;
        sourceChatName: string;
        originalMessageId?: string;
        additionalMembers?: string[];
    }): Promise<StartWorkflowResult>;
    private createResearchChatWithRetry;
    private addMembersWithFallback;
    completeWorkflow(requirementId: string, chatContext?: string): Promise<CompleteWorkflowResult>;
    private generatePRD;
    getApi(): FeishuAPI;
    getBitable(): BitableClient;
}
export declare function startRequirementFollow(params: {
    requirementContent: string;
    requesterName: string;
    requesterId: string;
    sourceChatId: string;
    sourceChatName: string;
    originalMessageId?: string;
    additionalMembers?: string[];
    config?: RequirementFollowConfig;
}): Promise<StartWorkflowResult>;
export declare function completeRequirementFollow(requirementId: string, chatContext?: string, config?: RequirementFollowConfig): Promise<CompleteWorkflowResult>;
export default RequirementFollowWorkflow;
//# sourceMappingURL=index.d.ts.map
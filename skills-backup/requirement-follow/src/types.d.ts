/**
 * Type declarations for requirement-follow skill
 * For use when importing from feishu-feedback-handler
 */

export interface StartWorkflowResult {
  success: boolean;
  isDuplicate?: boolean;
  recordId?: string;
  chatId?: string;
  chatName?: string;
  error?: string;
  existingRecordId?: string;
}

export interface RequirementFollowConfig {
  appId: string;
  appSecret: string;
  requirementTableId: string;
  requirementAppToken: string;
  bossId: string;
}

export interface StartWorkflowParams {
  requirementContent: string;
  requesterName: string;
  requesterId: string;
  sourceChatId: string;
  sourceChatName: string;
  originalMessageId?: string;
  additionalMembers?: string[];
}

export declare class RequirementFollowWorkflow {
  constructor(config: RequirementFollowConfig);
  startWorkflow(params: StartWorkflowParams): Promise<StartWorkflowResult>;
  getApi(): any;
  getBitable(): any;
}

export declare function getDefaultConfig(): RequirementFollowConfig | null;
export declare function startRequirementFollow(params: StartWorkflowParams): Promise<StartWorkflowResult>;

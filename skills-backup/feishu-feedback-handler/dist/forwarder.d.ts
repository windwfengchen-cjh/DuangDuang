/**
 * 消息转发逻辑模块
 * 从 auto_forward.py 移植
 */
import { FullConfig } from './config';
/**
 * 消息类型
 */
export type MessageType = '问题' | '需求' | '咨询';
/**
 * 转发参数
 */
export interface ForwardParams {
    sourceChat: string;
    reporter: string;
    content: string;
    messageType: MessageType;
    sourceChatId: string;
    messageId: string;
    imageKey?: string;
    recordBitable: boolean;
}
/**
 * 转发结果
 */
export interface ForwardResult {
    success: boolean;
    error?: string;
    imageForwarded?: boolean;
    recordId?: string;
}
/**
 * 回复转发参数
 */
export interface ReplyForwardParams {
    matchedRecord: any;
    status: string;
    result: string;
    senderName: string;
}
/**
 * 转发器类
 */
export declare class Forwarder {
    private config;
    private token;
    private contacts;
    constructor(config: FullConfig);
    /**
     * 设置 Token
     */
    setToken(token: string): void;
    /**
     * 获取按日期命名的日志文件路径
     */
    private getLogFilePath;
    /**
     * 清理超过1天的旧日志文件
     */
    private cleanupOldLogs;
    /**
     * 记录转发报文日志
     */
    private logForwardPayload;
    /**
     * 加载联系人映射
     */
    private loadContacts;
    /**
     * 根据姓名获取用户ID
     */
    private getUserIdByName;
    /**
     * 下载图片 - 使用 Resource API（支持下载任何人发的图片）
     * @param messageId 消息ID
     * @param fileKey 文件/图片key
     */
    private downloadImageByResource;
    /**
     * 下载图片 - 兼容旧版（使用 Images API，只能下载自己发的图片）
     * @deprecated 请使用 downloadImageByResource
     */
    private downloadImage;
    /**
     * 上传图片到飞书
     */
    private uploadImage;
    /**
     * 构建表单数据
     */
    private buildFormData;
    /**
     * 转发消息
     */
    forwardMessage(params: ForwardParams): Promise<ForwardResult>;
    /**
     * 验证@人员配置是否有效
     * 确保 user_id 和 user_name 都不为空
     */
    private validateAtList;
    /**
     * 发送 Post 消息
     */
    private sendPostMessage;
    /**
     * 转发回复到来源群
     */
    forwardReplyToSource(params: ReplyForwardParams): Promise<boolean>;
    /**
     * 获取转发配置
     */
    private getForwardConfig;
}
export default Forwarder;
//# sourceMappingURL=forwarder.d.ts.map
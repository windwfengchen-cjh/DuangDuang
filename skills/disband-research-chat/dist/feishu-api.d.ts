import { FeishuCredentials } from './config';
import Logger from './logger';
/**
 * 飞书 API 响应接口
 */
interface FeishuResponse<T = any> {
    code: number;
    msg: string;
    data?: T;
}
/**
 * 飞书 API 客户端类
 */
export declare class FeishuAPI {
    private client;
    private credentials;
    private tenantToken;
    private tokenExpireTime;
    private logger;
    constructor(credentials: FeishuCredentials, logger: Logger);
    /**
     * 获取租户访问令牌
     */
    getTenantAccessToken(): Promise<string>;
    /**
     * 解散群组
     */
    disbandChat(chatId: string): Promise<FeishuResponse>;
    /**
     * 获取群组信息（用于验证群是否存在）
     */
    getChatInfo(chatId: string): Promise<FeishuResponse>;
}
export default FeishuAPI;
//# sourceMappingURL=feishu-api.d.ts.map
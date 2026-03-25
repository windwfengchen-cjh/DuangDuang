"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FeishuAPI = void 0;
const axios_1 = __importDefault(require("axios"));
/**
 * 飞书 API 客户端类
 */
class FeishuAPI {
    constructor(credentials, logger) {
        this.tenantToken = null;
        this.tokenExpireTime = 0;
        this.credentials = credentials;
        this.logger = logger;
        this.client = axios_1.default.create({
            baseURL: 'https://open.feishu.cn/open-apis',
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        // 请求拦截器 - 添加认证头
        this.client.interceptors.request.use(async (config) => {
            const token = await this.getTenantAccessToken();
            config.headers.Authorization = `Bearer ${token}`;
            return config;
        }, (error) => Promise.reject(error));
        // 响应拦截器 - 统一错误处理
        this.client.interceptors.response.use((response) => response.data, (error) => {
            this.logger.error('API request failed', {
                url: error.config?.url,
                method: error.config?.method,
                status: error.response?.status,
                code: error.response?.data?.code,
                msg: error.response?.data?.msg
            });
            return Promise.reject(error);
        });
    }
    /**
     * 获取租户访问令牌
     */
    async getTenantAccessToken() {
        // 检查令牌是否有效
        const now = Date.now();
        if (this.tenantToken && this.tokenExpireTime > now + 60000) {
            return this.tenantToken;
        }
        try {
            this.logger.debug('Fetching tenant access token');
            const response = await axios_1.default.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', {
                app_id: this.credentials.app_id,
                app_secret: this.credentials.app_secret
            }, {
                headers: { 'Content-Type': 'application/json' }
            });
            // 注意：飞书API返回的数据直接在根级别
            const data = response.data;
            if (data.code !== 0) {
                throw new Error(`Token error: ${data.msg} (code: ${data.code})`);
            }
            if (!data.tenant_access_token) {
                throw new Error('Token response missing tenant_access_token');
            }
            this.tenantToken = data.tenant_access_token;
            this.tokenExpireTime = now + (data.expire * 1000);
            this.logger.debug('Token obtained successfully', {
                expireIn: data.expire
            });
            return data.tenant_access_token;
        }
        catch (error) {
            this.logger.error('Failed to get tenant access token', {
                error: error instanceof Error ? error.message : String(error)
            });
            throw error;
        }
    }
    /**
     * 解散群组
     */
    async disbandChat(chatId) {
        try {
            this.logger.info('Disbanding chat', { chatId });
            const response = await this.client.delete(`/im/v1/chats/${chatId}`);
            const data = response.data;
            if (data.code !== 0) {
                this.logger.error('Failed to disband chat', {
                    chatId,
                    code: data.code,
                    msg: data.msg
                });
                throw new Error(`Disband failed: ${data.msg} (code: ${data.code})`);
            }
            this.logger.info('Chat disbanded successfully', { chatId });
            return data;
        }
        catch (error) {
            if (axios_1.default.isAxiosError(error)) {
                const axiosError = error;
                const errorCode = axiosError.response?.data?.code;
                const errorMsg = axiosError.response?.data?.msg || axiosError.message;
                // 处理特定错误码
                if (errorCode === 9499) {
                    throw new Error('权限不足，无法解散该群组。请确保应用有 chat:manage 权限');
                }
                else if (errorCode === 230004) {
                    throw new Error('群组不存在或已被解散');
                }
                else if (errorCode === 230001) {
                    throw new Error('无效的群ID');
                }
                throw new Error(`API Error: ${errorMsg} (code: ${errorCode || 'unknown'})`);
            }
            throw error;
        }
    }
    /**
     * 获取群组信息（用于验证群是否存在）
     */
    async getChatInfo(chatId) {
        try {
            const response = await this.client.get(`/im/v1/chats/${chatId}`);
            return response.data;
        }
        catch (error) {
            if (axios_1.default.isAxiosError(error)) {
                const axiosError = error;
                return {
                    code: axiosError.response?.data?.code || -1,
                    msg: axiosError.response?.data?.msg || 'Unknown error'
                };
            }
            throw error;
        }
    }
}
exports.FeishuAPI = FeishuAPI;
exports.default = FeishuAPI;
//# sourceMappingURL=feishu-api.js.map
import axios, { AxiosInstance, AxiosError } from 'axios';
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
 * 访问令牌响应
 * 注意：飞书API返回的token直接在根级别，不在data字段中
 */
interface TokenResponse {
  code: number;
  msg: string;
  tenant_access_token: string;
  expire: number;
}

/**
 * 飞书 API 客户端类
 */
export class FeishuAPI {
  private client: AxiosInstance;
  private credentials: FeishuCredentials;
  private tenantToken: string | null = null;
  private tokenExpireTime: number = 0;
  private logger: Logger;

  constructor(credentials: FeishuCredentials, logger: Logger) {
    this.credentials = credentials;
    this.logger = logger;
    
    this.client = axios.create({
      baseURL: 'https://open.feishu.cn/open-apis',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 请求拦截器 - 添加认证头
    this.client.interceptors.request.use(
      async (config) => {
        const token = await this.getTenantAccessToken();
        config.headers.Authorization = `Bearer ${token}`;
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 统一错误处理
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError<FeishuResponse>) => {
        this.logger.error('API request failed', {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          code: error.response?.data?.code,
          msg: error.response?.data?.msg
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * 获取租户访问令牌
   */
  async getTenantAccessToken(): Promise<string> {
    // 检查令牌是否有效
    const now = Date.now();
    if (this.tenantToken && this.tokenExpireTime > now + 60000) {
      return this.tenantToken;
    }

    try {
      this.logger.debug('Fetching tenant access token');
      
      const response = await axios.post<FeishuResponse<TokenResponse>>(
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        {
          app_id: this.credentials.app_id,
          app_secret: this.credentials.app_secret
        },
        {
          headers: { 'Content-Type': 'application/json' }
        }
      );

      // 注意：飞书API返回的数据直接在根级别
      const data = response.data as any;
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
    } catch (error) {
      this.logger.error('Failed to get tenant access token', {
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * 解散群组
   */
  async disbandChat(chatId: string): Promise<FeishuResponse> {
    try {
      this.logger.info('Disbanding chat', { chatId });

      const response = await this.client.delete<FeishuResponse>(`/im/v1/chats/${chatId}`);
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
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<FeishuResponse>;
        const errorCode = axiosError.response?.data?.code;
        const errorMsg = axiosError.response?.data?.msg || axiosError.message;

        // 处理特定错误码
        if (errorCode === 9499) {
          throw new Error('权限不足，无法解散该群组。请确保应用有 chat:manage 权限');
        } else if (errorCode === 230004) {
          throw new Error('群组不存在或已被解散');
        } else if (errorCode === 230001) {
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
  async getChatInfo(chatId: string): Promise<FeishuResponse> {
    try {
      const response = await this.client.get<FeishuResponse>(`/im/v1/chats/${chatId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<FeishuResponse>;
        return {
          code: axiosError.response?.data?.code || -1,
          msg: axiosError.response?.data?.msg || 'Unknown error'
        };
      }
      throw error;
    }
  }
}

export default FeishuAPI;

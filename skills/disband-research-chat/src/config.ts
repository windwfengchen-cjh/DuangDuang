import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * 飞书应用凭证配置
 */
export interface FeishuCredentials {
  app_id: string;
  app_secret: string;
}

/**
 * Skill 配置接口
 */
export interface SkillConfig {
  credentials: FeishuCredentials;
  apiBaseUrl: string;
  logPath: string;
}

/**
 * 错误码定义
 */
export enum ErrorCode {
  SUCCESS = 0,
  CONFIG_NOT_FOUND = 1001,
  CONFIG_INVALID = 1002,
  CREDENTIALS_INVALID = 1003,
  CHAT_ID_INVALID = 1004,
  CHAT_ID_MISSING = 1005,
  API_ERROR = 2001,
  TOKEN_ERROR = 2002,
  DISBAND_FAILED = 2003,
  PERMISSION_DENIED = 2004,
  NETWORK_ERROR = 3001,
  UNKNOWN_ERROR = 9999
}

/**
 * 错误信息映射
 */
export const ErrorMessages: Record<ErrorCode, string> = {
  [ErrorCode.SUCCESS]: '操作成功',
  [ErrorCode.CONFIG_NOT_FOUND]: '未找到配置文件 ~/.openclaw/openclaw.json',
  [ErrorCode.CONFIG_INVALID]: '配置文件格式错误',
  [ErrorCode.CREDENTIALS_INVALID]: '飞书凭证无效，请检查 app_id 和 app_secret',
  [ErrorCode.CHAT_ID_INVALID]: '群ID格式无效，应以 "oc_" 开头',
  [ErrorCode.CHAT_ID_MISSING]: '未提供群ID，请使用 --chat-id 参数或 DISBAND_CHAT_ID 环境变量',
  [ErrorCode.API_ERROR]: '飞书 API 调用失败',
  [ErrorCode.TOKEN_ERROR]: '获取访问令牌失败',
  [ErrorCode.DISBAND_FAILED]: '解散群组失败',
  [ErrorCode.PERMISSION_DENIED]: '权限不足，无法解散该群组',
  [ErrorCode.NETWORK_ERROR]: '网络连接错误',
  [ErrorCode.UNKNOWN_ERROR]: '未知错误'
};

/**
 * 配置管理器类
 */
export class ConfigManager {
  private configPath: string;
  private config: SkillConfig | null = null;

  constructor() {
    this.configPath = path.join(os.homedir(), '.openclaw', 'openclaw.json');
  }

  /**
   * 加载配置文件
   */
  loadConfig(): SkillConfig {
    try {
      if (!fs.existsSync(this.configPath)) {
        throw new Error(ErrorMessages[ErrorCode.CONFIG_NOT_FOUND]);
      }

      const content = fs.readFileSync(this.configPath, 'utf-8');
      const data = JSON.parse(content);

      // 支持多种配置格式
      // 格式1: { "app_id": "xxx", "app_secret": "xxx" }
      // 格式2: { "appId": "xxx", "appSecret": "xxx" }
      // 格式3: { "channels": { "feishu": { "app_id/appId": "xxx", "app_secret/appSecret": "xxx" } } }
      let app_id = data.app_id || data.appId;
      let app_secret = data.app_secret || data.appSecret;

      if (!app_id || !app_secret) {
        const feishuConfig = data.channels?.feishu;
        if (feishuConfig) {
          app_id = feishuConfig.app_id || feishuConfig.appId;
          app_secret = feishuConfig.app_secret || feishuConfig.appSecret;
        }
      }

      if (!app_id || !app_secret) {
        throw new Error(ErrorMessages[ErrorCode.CREDENTIALS_INVALID]);
      }

      this.config = {
        credentials: {
          app_id: app_id,
          app_secret: app_secret
        },
        apiBaseUrl: 'https://open.feishu.cn/open-apis',
        logPath: path.join(os.homedir(), '.openclaw', 'logs', 'disband-research-chat.log')
      };

      return this.config;
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error(`${ErrorMessages[ErrorCode.CONFIG_INVALID]}: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * 获取配置
   */
  getConfig(): SkillConfig {
    if (!this.config) {
      return this.loadConfig();
    }
    return this.config;
  }

  /**
   * 验证群ID格式
   */
  validateChatId(chatId: string): boolean {
    // 飞书群ID格式：oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    const pattern = /^oc_[a-f0-9]{32}$/;
    return pattern.test(chatId);
  }

  /**
   * 确保日志目录存在
   */
  ensureLogDir(): void {
    if (!this.config) return;
    const logDir = path.dirname(this.config.logPath);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }
}

export default ConfigManager;

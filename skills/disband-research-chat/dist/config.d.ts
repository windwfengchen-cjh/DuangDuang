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
export declare enum ErrorCode {
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
export declare const ErrorMessages: Record<ErrorCode, string>;
/**
 * 配置管理器类
 */
export declare class ConfigManager {
    private configPath;
    private config;
    constructor();
    /**
     * 加载配置文件
     */
    loadConfig(): SkillConfig;
    /**
     * 获取配置
     */
    getConfig(): SkillConfig;
    /**
     * 验证群ID格式
     */
    validateChatId(chatId: string): boolean;
    /**
     * 确保日志目录存在
     */
    ensureLogDir(): void;
}
export default ConfigManager;
//# sourceMappingURL=config.d.ts.map
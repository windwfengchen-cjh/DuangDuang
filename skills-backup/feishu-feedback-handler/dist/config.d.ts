/**
 * 配置管理模块
 * 从外部配置文件读取 forward_configs
 */
/**
 * 处理人配置
 */
export interface HandlerConfig {
    user_id: string;
    user_name: string;
}
/**
 * 转发配置
 */
export interface ForwardConfig {
    target_chat_id: string;
    handlers: HandlerConfig[];
    source_name: string;
    record_bitable: boolean;
    notify_boss_for_requirement: boolean;
}
/**
 * 飞书凭证
 */
export interface FeishuCreds {
    appId: string;
    appSecret: string;
}
/**
 * 多维表格配置
 */
export interface BitableConfig {
    app_token: string;
    table_id: string;
}
/**
 * Bot 配置
 */
export interface BotConfig {
    bot_id: string;
}
/**
 * Boss 配置
 */
export interface BossConfig {
    user_id: string;
    user_name: string;
}
/**
 * 完整配置
 */
export interface FullConfig {
    feishuCreds: FeishuCreds;
    bitable: BitableConfig;
    bot: BotConfig;
    boss: BossConfig;
    forwardConfigs: Record<string, ForwardConfig>;
}
/**
 * 从 OpenClaw 配置加载飞书凭证
 */
export declare function loadFeishuCreds(): FeishuCreds;
/**
 * 从 config.json 加载 Skill 配置
 */
export declare function loadSkillConfig(): any;
/**
 * 加载完整配置
 */
export declare function loadConfig(): FullConfig;
/**
 * 根据来源群ID获取转发配置
 */
export declare function getForwardConfig(configs: Record<string, ForwardConfig>, sourceChatId: string): ForwardConfig | null;
/**
 * 保存用户配置
 */
export declare function saveUserConfig(config: any): void;
/**
 * 验证配置是否完整
 */
export declare function validateConfig(config: FullConfig): {
    valid: boolean;
    errors: string[];
};
//# sourceMappingURL=config.d.ts.map
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigManager = exports.ErrorMessages = exports.ErrorCode = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
/**
 * 错误码定义
 */
var ErrorCode;
(function (ErrorCode) {
    ErrorCode[ErrorCode["SUCCESS"] = 0] = "SUCCESS";
    ErrorCode[ErrorCode["CONFIG_NOT_FOUND"] = 1001] = "CONFIG_NOT_FOUND";
    ErrorCode[ErrorCode["CONFIG_INVALID"] = 1002] = "CONFIG_INVALID";
    ErrorCode[ErrorCode["CREDENTIALS_INVALID"] = 1003] = "CREDENTIALS_INVALID";
    ErrorCode[ErrorCode["CHAT_ID_INVALID"] = 1004] = "CHAT_ID_INVALID";
    ErrorCode[ErrorCode["CHAT_ID_MISSING"] = 1005] = "CHAT_ID_MISSING";
    ErrorCode[ErrorCode["API_ERROR"] = 2001] = "API_ERROR";
    ErrorCode[ErrorCode["TOKEN_ERROR"] = 2002] = "TOKEN_ERROR";
    ErrorCode[ErrorCode["DISBAND_FAILED"] = 2003] = "DISBAND_FAILED";
    ErrorCode[ErrorCode["PERMISSION_DENIED"] = 2004] = "PERMISSION_DENIED";
    ErrorCode[ErrorCode["NETWORK_ERROR"] = 3001] = "NETWORK_ERROR";
    ErrorCode[ErrorCode["UNKNOWN_ERROR"] = 9999] = "UNKNOWN_ERROR";
})(ErrorCode || (exports.ErrorCode = ErrorCode = {}));
/**
 * 错误信息映射
 */
exports.ErrorMessages = {
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
class ConfigManager {
    constructor() {
        this.config = null;
        this.configPath = path.join(os.homedir(), '.openclaw', 'openclaw.json');
    }
    /**
     * 加载配置文件
     */
    loadConfig() {
        try {
            if (!fs.existsSync(this.configPath)) {
                throw new Error(exports.ErrorMessages[ErrorCode.CONFIG_NOT_FOUND]);
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
                throw new Error(exports.ErrorMessages[ErrorCode.CREDENTIALS_INVALID]);
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
        }
        catch (error) {
            if (error instanceof SyntaxError) {
                throw new Error(`${exports.ErrorMessages[ErrorCode.CONFIG_INVALID]}: ${error.message}`);
            }
            throw error;
        }
    }
    /**
     * 获取配置
     */
    getConfig() {
        if (!this.config) {
            return this.loadConfig();
        }
        return this.config;
    }
    /**
     * 验证群ID格式
     */
    validateChatId(chatId) {
        // 飞书群ID格式：oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        const pattern = /^oc_[a-f0-9]{32}$/;
        return pattern.test(chatId);
    }
    /**
     * 确保日志目录存在
     */
    ensureLogDir() {
        if (!this.config)
            return;
        const logDir = path.dirname(this.config.logPath);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }
}
exports.ConfigManager = ConfigManager;
exports.default = ConfigManager;
//# sourceMappingURL=config.js.map
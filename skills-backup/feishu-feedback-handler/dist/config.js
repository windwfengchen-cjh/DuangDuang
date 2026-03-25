"use strict";
/**
 * 配置管理模块
 * 从外部配置文件读取 forward_configs
 */
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
exports.loadFeishuCreds = loadFeishuCreds;
exports.loadSkillConfig = loadSkillConfig;
exports.loadConfig = loadConfig;
exports.getForwardConfig = getForwardConfig;
exports.saveUserConfig = saveUserConfig;
exports.validateConfig = validateConfig;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
// 配置文件路径
const SKILL_DIR = path.resolve(__dirname, '..');
const CONFIG_PATH = path.join(SKILL_DIR, 'config.json');
const OPENCLAW_CONFIG_PATH = path.join(process.env.HOME || '', '.openclaw', 'openclaw.json');
/**
 * 从 OpenClaw 配置加载飞书凭证
 */
function loadFeishuCreds() {
    try {
        const configContent = fs.readFileSync(OPENCLAW_CONFIG_PATH, 'utf-8');
        const config = JSON.parse(configContent);
        const feishuConfig = config.channels?.feishu || {};
        return {
            appId: feishuConfig.appId || '',
            appSecret: feishuConfig.appSecret || ''
        };
    }
    catch (e) {
        console.error('加载飞书凭证失败:', e);
        return { appId: '', appSecret: '' };
    }
}
/**
 * 从 config.json 加载 Skill 配置
 */
function loadSkillConfig() {
    try {
        if (fs.existsSync(CONFIG_PATH)) {
            const configContent = fs.readFileSync(CONFIG_PATH, 'utf-8');
            return JSON.parse(configContent);
        }
        else {
            console.error('配置文件不存在:', CONFIG_PATH);
            console.error('请复制 config.json.example 为 config.json 并填写配置');
            return {};
        }
    }
    catch (e) {
        console.error('加载 Skill 配置失败:', e);
        return {};
    }
}
/**
 * 加载完整配置
 */
function loadConfig() {
    const feishuCreds = loadFeishuCreds();
    const skillConfig = loadSkillConfig();
    // 验证必要配置是否存在
    if (!skillConfig.forward_configs) {
        console.error('配置错误: forward_configs 未定义');
    }
    if (!skillConfig.bitable) {
        console.error('配置错误: bitable 未定义');
    }
    if (!skillConfig.boss) {
        console.error('配置错误: boss 未定义');
    }
    return {
        feishuCreds,
        bitable: skillConfig.bitable || { app_token: '', table_id: '' },
        bot: skillConfig.bot || { bot_id: '' },
        boss: skillConfig.boss || { user_id: '', user_name: '' },
        forwardConfigs: skillConfig.forward_configs || {}
    };
}
/**
 * 根据来源群ID获取转发配置
 */
function getForwardConfig(configs, sourceChatId) {
    const config = configs[sourceChatId];
    if (config) {
        // 过滤掉没有 user_id 的处理人
        return {
            ...config,
            handlers: config.handlers.filter(h => h.user_id)
        };
    }
    // 未找到配置，返回 null
    console.error(`未找到来源群配置: ${sourceChatId}`);
    return null;
}
/**
 * 保存用户配置
 */
function saveUserConfig(config) {
    const userConfigPath = path.join(SKILL_DIR, 'config.json');
    try {
        fs.writeFileSync(userConfigPath, JSON.stringify(config, null, 2), 'utf-8');
        console.log('配置已保存');
    }
    catch (e) {
        console.error('保存配置失败:', e);
        throw e;
    }
}
/**
 * 验证配置是否完整
 */
function validateConfig(config) {
    const errors = [];
    if (!config.feishuCreds.appId) {
        errors.push('缺少飞书 App ID');
    }
    if (!config.feishuCreds.appSecret) {
        errors.push('缺少飞书 App Secret');
    }
    if (!config.bitable.app_token) {
        errors.push('缺少多维表格 App Token');
    }
    if (!config.bitable.table_id) {
        errors.push('缺少多维表格 Table ID');
    }
    if (!config.bot.bot_id) {
        errors.push('缺少 Bot ID');
    }
    if (Object.keys(config.forwardConfigs).length === 0) {
        errors.push('缺少转发配置');
    }
    return {
        valid: errors.length === 0,
        errors
    };
}
//# sourceMappingURL=config.js.map
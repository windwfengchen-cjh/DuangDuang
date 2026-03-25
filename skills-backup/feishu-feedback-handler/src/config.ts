/**
 * 配置管理模块
 * 从外部配置文件读取 forward_configs
 */

import * as fs from 'fs';
import * as path from 'path';

// 配置文件路径
const SKILL_DIR = path.resolve(__dirname, '..');
const CONFIG_PATH = path.join(SKILL_DIR, 'config.json');
const OPENCLAW_CONFIG_PATH = path.join(process.env.HOME || '', '.openclaw', 'openclaw.json');

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
export function loadFeishuCreds(): FeishuCreds {
  try {
    const configContent = fs.readFileSync(OPENCLAW_CONFIG_PATH, 'utf-8');
    const config = JSON.parse(configContent);
    const feishuConfig = config.channels?.feishu || {};
    
    return {
      appId: feishuConfig.appId || '',
      appSecret: feishuConfig.appSecret || ''
    };
  } catch (e) {
    console.error('加载飞书凭证失败:', e);
    return { appId: '', appSecret: '' };
  }
}

/**
 * 从 config.json 加载 Skill 配置
 */
export function loadSkillConfig(): any {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const configContent = fs.readFileSync(CONFIG_PATH, 'utf-8');
      return JSON.parse(configContent);
    } else {
      console.error('配置文件不存在:', CONFIG_PATH);
      console.error('请复制 config.json.example 为 config.json 并填写配置');
      return {};
    }
  } catch (e) {
    console.error('加载 Skill 配置失败:', e);
    return {};
  }
}

/**
 * 加载完整配置
 */
export function loadConfig(): FullConfig {
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
export function getForwardConfig(
  configs: Record<string, ForwardConfig>,
  sourceChatId: string
): ForwardConfig | null {
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
export function saveUserConfig(config: any): void {
  const userConfigPath = path.join(SKILL_DIR, 'config.json');
  try {
    fs.writeFileSync(userConfigPath, JSON.stringify(config, null, 2), 'utf-8');
    console.log('配置已保存');
  } catch (e) {
    console.error('保存配置失败:', e);
    throw e;
  }
}

/**
 * 验证配置是否完整
 */
export function validateConfig(config: FullConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

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

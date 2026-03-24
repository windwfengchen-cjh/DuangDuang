import * as fs from 'fs';
import * as path from 'path';

const OPENCLAW_CONFIG = path.join(process.env.HOME || '', '.openclaw', 'openclaw.json');

/**
 * 从 OpenClaw 配置加载飞书凭证
 */
export async function loadFeishuCreds(): Promise<{ appId: string | null; appSecret: string | null }> {
  try {
    const config = JSON.parse(fs.readFileSync(OPENCLAW_CONFIG, 'utf-8'));
    const feishuConfig = config.channels?.feishu || {};
    return {
      appId: feishuConfig.appId || null,
      appSecret: feishuConfig.appSecret || null
    };
  } catch (error) {
    console.error('❌ 加载配置失败:', error);
    return { appId: null, appSecret: null };
  }
}

/**
 * 获取飞书 tenant_access_token
 */
export async function getTenantAccessToken(): Promise<string> {
  const { appId, appSecret } = await loadFeishuCreds();
  
  if (!appId || !appSecret) {
    throw new Error('无法获取飞书凭证');
  }

  const url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal';
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_id: appId, app_secret: appSecret })
  });

  const data = await response.json();
  if (data.code !== 0) {
    throw new Error(`获取 token 失败: ${JSON.stringify(data)}`);
  }

  return data.tenant_access_token;
}

/**
 * 从 contacts.json 查找用户 Open ID
 */
export function getUserIdByName(userName: string): string | null {
  try {
    const contactsPath = path.join(__dirname, '..', 'references', 'contacts.json');
    if (!fs.existsSync(contactsPath)) return null;
    
    const contacts = JSON.parse(fs.readFileSync(contactsPath, 'utf-8'));
    
    for (const [userId, info] of Object.entries(contacts)) {
      if (typeof info === 'object' && info !== null) {
        if ((info as any).name === userName) return userId;
      } else if (info === userName) {
        return userId;
      }
    }
    return null;
  } catch (error) {
    console.error('⚠️ 查找用户ID失败:', error);
    return null;
  }
}

/**
 * 构建飞书 @ 标签
 */
export function buildAtTag(userName: string): any {
  const userId = getUserIdByName(userName);
  
  if (userId) {
    return {
      tag: 'at',
      user_id: userId,
      user_name: userName
    };
  }
  
  // 找不到 ID，用纯文本
  return {
    tag: 'text',
    text: `@${userName}`
  };
}

/**
 * 检查消息是否 @ 我
 */
export function isAtMe(messageText: string, botId: string): boolean {
  return messageText.includes(`<at user_id="${botId}">`);
}

/**
 * 移除消息中的 @ 标签
 */
export function removeAtTags(messageText: string): string {
  return messageText
    .replace(/<at[^>]*>[^<]*<\/at>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * 提取状态和处理结果
 */
export function extractStatusAndResult(messageText: string): { status: string | null; result: string } {
  const statusKeywords: Record<string, string> = {
    '已解决': '已解决',
    '已完成': '已解决',
    '搞定': '已解决',
    '已修复': '已解决',
    'ok': '已解决',
    'OK': '已解决',
    '已处理': '已解决',
    '解决了': '已解决',
    '完成了': '已解决',
    '处理好了': '已解决',
    '同步好了': '已解决',
    '已关闭': '已关闭',
    '无需处理': '已关闭',
    '重复问题': '已关闭',
    '处理中': '处理中',
    '正在处理': '处理中',
    '跟进中': '处理中',
    '待处理': '待处理',
    '已上线': '已解决',
    '上线': '已解决'
  };

  for (const [keyword, status] of Object.entries(statusKeywords)) {
    if (messageText.includes(keyword)) {
      // 提取包含关键词的句子
      const sentences = messageText.split(/[。！？\n]/);
      for (const sent of sentences) {
        if (sent.includes(keyword)) {
          return { status, result: sent.trim() };
        }
      }
      return { status, result: messageText.slice(0, 100) };
    }
  }

  return { status: null, result: messageText.slice(0, 100) };
}

/**
 * 提取问题关键词
 */
export function extractIssueKeywords(messageText: string): string[] {
  const keywords = [
    '同步', '数据', '订单', '导入', 'CSV', '派卡', '公众号',
    '通知', '抢单', '交付', '系统', '接口', '历史订单',
    '重新同步', '统计', '配置', '关闭', '统计', '填单'
  ];
  
  return keywords.filter(kw => messageText.includes(kw));
}

/**
 * 延迟函数
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 格式化日期
 */
export function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toISOString().replace('T', ' ').slice(0, 19);
}

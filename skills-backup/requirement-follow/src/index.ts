/**
 * Requirement Follow Skill - 完整需求跟进解决方案
 * 版本：3.0.0 - 整合自 requirement_follow.py
 */

import * as fs from 'fs';
import * as path from 'path';
import { FeishuAPI, ChatInfo } from './api';
import { BitableClient } from './bitable';

// 重新导出原有模块（保持兼容性）
export * from './research';

// 导入调研模块函数
import { createResearchSession, startResearch, pollResearchChat, startResearchPolling, getActiveResearchSessions, loadResearchSession } from './research';

export { FeishuAPI, BitableClient };

// 默认配置
const DEFAULT_REQUIREMENT_TABLE_ID = 'tbl0vJo8gPHIeZ9y';
const DEFAULT_REQUIREMENT_APP_TOKEN = 'Op8WbbFewaq1tasfO8IcQkXmnFf';
const DEFAULT_BOSS_ID = 'ou_3e48baef1bd71cc89fb5a364be55cafc';

const PRD_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'prd');
if (!fs.existsSync(PRD_DIR)) fs.mkdirSync(PRD_DIR, { recursive: true });

// ==================== 类型定义 ====================

export interface RequirementFollowConfig {
  appId: string;
  appSecret: string;
  requirementTableId: string;
  requirementAppToken: string;
  bossId: string;
}

export interface StartWorkflowResult {
  success: boolean;
  isDuplicate?: boolean;
  recordId?: string;
  chatId?: string;
  chatName?: string;
  error?: string;
  existingRecordId?: string;
}

export interface CompleteWorkflowResult {
  success: boolean;
  requirementId?: string;
  prdPath?: string;
  chatDisbanded?: boolean;
  error?: string;
}

// ==================== 配置加载 ====================

function loadFeishuCreds(): { appId: string; appSecret: string } | null {
  try {
    const configPath = path.join(process.env.HOME || '', '.openclaw', 'openclaw.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    // 尝试多种可能的路径
    const feishuConfig = config.plugins?.channels?.feishu || config.channels?.feishu || {};
    if (feishuConfig.appId && feishuConfig.appSecret) {
      return { appId: feishuConfig.appId, appSecret: feishuConfig.appSecret };
    }
  } catch (e) {
    console.error('❌ 加载配置失败:', e);
  }
  return null;
}

export function getDefaultConfig(): RequirementFollowConfig | null {
  const creds = loadFeishuCreds();
  if (!creds) return null;
  return {
    appId: creds.appId,
    appSecret: creds.appSecret,
    requirementTableId: process.env.REQUIREMENT_TABLE_ID || DEFAULT_REQUIREMENT_TABLE_ID,
    requirementAppToken: process.env.REQUIREMENT_APP_TOKEN || DEFAULT_REQUIREMENT_APP_TOKEN,
    bossId: process.env.BOSS_ID || DEFAULT_BOSS_ID
  };
}

// ==================== 工作流类 ====================

export class RequirementFollowWorkflow {
  private api: FeishuAPI;
  private bitable: BitableClient;
  private config: RequirementFollowConfig;

  constructor(config: RequirementFollowConfig) {
    this.config = config;
    this.api = new FeishuAPI({ appId: config.appId, appSecret: config.appSecret });
    this.bitable = new BitableClient({
      appToken: config.requirementAppToken,
      tableId: config.requirementTableId,
      feishuApi: this.api
    });
  }

  async startWorkflow(params: {
    requirementContent: string;
    requesterName: string;
    requesterId: string;
    sourceChatId: string;
    sourceChatName: string;
    originalMessageId?: string;
    additionalMembers?: string[];
  }): Promise<StartWorkflowResult> {
    console.log('='.repeat(60));
    console.log('🚀 启动需求跟进流程');
    console.log('='.repeat(60));
    console.log(`📨 需求内容: ${params.requirementContent.slice(0, 50)}...`);
    console.log(`👤 需求方: ${params.requesterName}`);

    // 检查重复需求
    const similar = await this.bitable.findSimilarRequirement(params.requirementContent);
    if (similar) {
      return {
        success: true,
        isDuplicate: true,
        existingRecordId: similar.record_id,
        error: `发现相似需求 (相似度: ${(similar.similarity * 100).toFixed(0)}%)`
      };
    }

    // 创建需求记录
    const recordId = await this.bitable.createRecord({
      requirementContent: params.requirementContent,
      requesterName: params.requesterName,
      requesterId: params.requesterId,
      sourceChatId: params.sourceChatId,
      sourceChatName: params.sourceChatName,
      originalMessageId: params.originalMessageId
    });

    if (!recordId) return { success: false, error: '创建需求记录失败' };

    // 准备成员列表（创建群后添加）
    const membersToAdd = [params.requesterId, this.config.bossId];
    if (params.additionalMembers) membersToAdd.push(...params.additionalMembers);
    const uniqueMembers = [...new Set(membersToAdd.filter(id => id))];

    // 创建调研群（只添加 Boss）
    const chatInfo = await this.createResearchChatWithRetry({
      requirementId: recordId,
      requirementContent: params.requirementContent,
      requesterName: params.requesterName,
      requesterId: params.requesterId
    });

    if (!chatInfo) {
      await this.bitable.updateRecord(recordId, { 需求状态: '创建失败', 调研群名称: '群创建失败' });
      return { success: false, error: '创建调研群失败', recordId };
    }

    // 验证群成员
    const validation = await this.api.validateChatMembers(chatInfo.chat_id, uniqueMembers);
    if (!validation.valid && validation.disbanded) {
      await this.bitable.updateRecord(recordId, { 需求状态: '创建失败', 调研群名称: '群成员验证失败' });
      return { success: false, error: '群成员验证失败', recordId };
    }

    // 更新记录关联调研群
    await this.bitable.updateResearchChat(recordId, chatInfo.chat_id, chatInfo.name);

    // 添加成员（尝试添加所有成员，失败的发送私信邀请）
    const addResult = await this.addMembersWithFallback(chatInfo.chat_id, uniqueMembers, {
      [params.requesterId]: params.requesterName,
      [this.config.bossId]: 'Boss'
    }, chatInfo.name, params.requesterId);

    // 如果需求方未成功入群，在群中发送提示消息
    if (addResult.requesterFailed) {
      const token = await this.api.getTenantAccessToken();
      await this.sendRequesterJoinNotice(chatInfo.chat_id, params.requesterName, token);
    }

    // 创建调研会话并启动调研流程
    let sessionCreated = false;
    try {
      const token = await this.api.getTenantAccessToken();
      
      // 创建调研会话（会自动保存到 ~/.openclaw/feishu/research/{chat_id}.json）
      createResearchSession(
        chatInfo.chat_id,
        params.requirementContent.slice(0, 100), // 需求标题（取内容前100字）
        params.requesterId,
        params.requesterName,
        this.config.bossId,
        recordId,
        'hybrid', // 默认使用混合模式（自动收集 + 问答）
        24 // 24小时自动收集截止时间
      );
      
      sessionCreated = true;
      console.log(`📝 调研会话已创建并保存到: ~/.openclaw/feishu/research/${chatInfo.chat_id}.json`);
      
      // 启动调研（发送欢迎消息和第一个问题）
      await startResearch(chatInfo.chat_id, token);
      
      console.log('🔔 调研流程已启动，等待需求方回复...');
      
      // 启动消息轮询（每5秒检查一次）
      this.startChatPolling(chatInfo.chat_id);
      
    } catch (researchError) {
      console.error('⚠️ 启动调研流程失败:', researchError);
      // 调研启动失败不影响整体流程，继续返回成功
    }

    console.log('✅ 需求跟进流程启动完成');

    return { success: true, recordId, chatId: chatInfo.chat_id, chatName: chatInfo.name };
  }

  private async createResearchChatWithRetry(params: { requirementId: string; requirementContent: string; requesterName: string; requesterId: string; maxRetries?: number }): Promise<ChatInfo | null> {
    const { requirementId, requirementContent, requesterName, requesterId, maxRetries = 2 } = params;
    const today = new Date().toISOString().slice(5, 10).replace('-', '');
    const chatName = `需求调研-${requesterName}-${today}`;
    const description = `需求调研群\n需求记录: ${requirementId}\n摘要: ${requirementContent.slice(0, 30)}...`;

    // 只添加对机器人可见的成员（Boss）
    const visibleMembers = [this.config.bossId].filter(id => id);

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 1) await new Promise(r => setTimeout(r, attempt * 3000));

        const chatInfo = await this.api.createChat({ name: chatName, description, chat_mode: 'group', chat_type: 'private', user_id_list: visibleMembers });
        await new Promise(r => setTimeout(r, 3000));

        const validation = await this.api.validateChatMembers(chatInfo.chat_id, visibleMembers);
        if (validation.valid) return chatInfo;
        if (validation.disbanded) continue;
        return chatInfo;
      } catch (e) {
        console.error(`第${attempt}次创建群失败:`, e);
      }
    }
    return null;
  }

  private async addMembersWithFallback(chatId: string, userIds: string[], userNames: Record<string, string>, chatName: string, requesterId: string): Promise<{ added: string[]; failed: string[]; requesterFailed: boolean }> {
    await new Promise(r => setTimeout(r, 5000));
    let result = await this.api.addMembersToChat(chatId, userIds);

    if (result.failed.length > 0) {
      await new Promise(r => setTimeout(r, 3000));
      const failedIds = result.failed.map(f => f.user_id);
      const retryResult = await this.api.addMembersToChat(chatId, failedIds);
      result.failed = retryResult.failed;
      result.added.push(...retryResult.added);
    }

    // 发送私信邀请给添加失败的成员
    for (const failed of result.failed) {
      await this.api.sendChatInvite(failed.user_id, chatId, chatName, { userName: userNames[failed.user_id] });
    }

    // 检查需求方是否成功入群
    const requesterFailed = result.failed.some(f => f.user_id === requesterId);
    const failedUserIds = result.failed.map(f => f.user_id);

    return { added: result.added, failed: failedUserIds, requesterFailed };
  }

  private async sendRequesterJoinNotice(chatId: string, requesterName: string, token: string): Promise<void> {
    try {
      const noticeText = `⚠️ **入群提示**\n\n@${requesterName} 可能由于隐私设置暂未入群。\n\n如果您是需求方，请：\n1. 检查私信中的群邀请链接，点击加入\n2. 或联系管理员手动添加您入群\n\n如已在群中，请忽略此消息。`;
      
      await fetch('https://open.feishu.cn/open-apis/im/v1/messages', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ 
          receive_id: chatId, 
          msg_type: 'text', 
          content: JSON.stringify({ text: noticeText }) 
        })
      });
    } catch (e) {
      console.error('发送入群提示失败:', e);
    }
  }

  async completeWorkflow(requirementId: string, chatContext: string = ''): Promise<CompleteWorkflowResult> {
    const record = await this.bitable.getRecord(requirementId);
    if (!record) return { success: false, error: '获取需求记录失败' };

    const fields = record.fields || record;
    const chatId = fields.调研群ID;

    // 生成 PRD
    const prdPath = await this.generatePRD({
      requirementId,
      requirementContent: fields.需求内容 || '',
      requester: fields.需求方 || 'Unknown',
      chatContext
    });

    if (!prdPath) return { success: false, error: '生成 PRD 失败' };

    await this.bitable.updateStatus(requirementId, '已完成', prdPath);

    let chatDisbanded = false;
    if (chatId) {
      await this.api.sendDisbandNotice(chatId);
      await new Promise(r => setTimeout(r, 3000));
      chatDisbanded = await this.api.disbandChat(chatId);
    }

    return { success: true, requirementId, prdPath, chatDisbanded };
  }

  private async generatePRD(params: { requirementId: string; requirementContent: string; requester: string; chatContext: string }): Promise<string | null> {
    const today = new Date().toISOString().split('T')[0];
    const prdPath = path.join(PRD_DIR, `prd-${params.requirementId}-${Date.now()}.md`);
    const content = `# PRD文档\n\n**需求ID**: ${params.requirementId}\n**需求方**: ${params.requester}\n**生成日期**: ${today}\n\n## 需求描述\n${params.requirementContent}\n\n## 调研记录\n${params.chatContext}\n`;
    try {
      fs.writeFileSync(prdPath, content, 'utf-8');
      console.log(`✅ PRD 文档已生成: ${prdPath}`);
      return prdPath;
    } catch (e) {
      console.error('生成 PRD 失败:', e);
      return null;
    }
  }

  getApi(): FeishuAPI { return this.api; }
  getBitable(): BitableClient { return this.bitable; }

  // 活跃的轮询定时器映射
  private pollTimers: Map<string, NodeJS.Timeout> = new Map();

  /**
   * 启动单个群的消息轮询
   * @param chatId 群ID
   * @param intervalMs 轮询间隔（毫秒），默认5000
   */
  startChatPolling(chatId: string, intervalMs: number = 5000): void {
    // 如果已有轮询，先停止
    this.stopChatPolling(chatId);
    
    console.log(`[${chatId}] 启动消息轮询，间隔 ${intervalMs}ms`);
    
    const poll = async () => {
      try {
        const session = loadResearchSession(chatId);
        // 允许 collecting 和 waiting_start 状态继续轮询
        if (!session || (session.status !== 'collecting' && session.status !== 'waiting_start')) {
          console.log(`[${chatId}] 会话已结束或不存在，停止轮询`);
          this.stopChatPolling(chatId);
          return;
        }
        
        await pollResearchChat(chatId, this.api, {
          onMessage: (cid, result) => {
            if (result.result?.action === 'completed') {
              console.log(`[${cid}] 调研完成，停止轮询`);
              this.stopChatPolling(cid);
            } else if (result.result?.action === 'cancelled') {
              console.log(`[${cid}] 调研已取消，停止轮询`);
              this.stopChatPolling(cid);
            }
          },
          onError: (cid, error) => {
            console.error(`[${cid}] 轮询错误:`, error.message);
          }
        });
        
        // 继续下次轮询
        if (this.pollTimers.has(chatId)) {
          this.pollTimers.set(chatId, setTimeout(poll, intervalMs));
        }
      } catch (error) {
        console.error(`[${chatId}] 轮询异常:`, error);
        // 出错后继续轮询
        if (this.pollTimers.has(chatId)) {
          this.pollTimers.set(chatId, setTimeout(poll, intervalMs));
        }
      }
    };
    
    // 启动第一次轮询
    this.pollTimers.set(chatId, setTimeout(poll, intervalMs));
  }

  /**
   * 停止单个群的消息轮询
   * @param chatId 群ID
   */
  stopChatPolling(chatId: string): void {
    const timer = this.pollTimers.get(chatId);
    if (timer) {
      clearTimeout(timer);
      this.pollTimers.delete(chatId);
      console.log(`[${chatId}] 消息轮询已停止`);
    }
  }

  /**
   * 停止所有消息轮询
   */
  stopAllPolling(): void {
    console.log(`停止所有消息轮询 (${this.pollTimers.size} 个)`);
    for (const [chatId, timer] of this.pollTimers) {
      clearTimeout(timer);
      console.log(`[${chatId}] 轮询已停止`);
    }
    this.pollTimers.clear();
  }
}

// ==================== 便捷函数 ====================

export async function startRequirementFollow(params: {
  requirementContent: string;
  requesterName: string;
  requesterId: string;
  sourceChatId: string;
  sourceChatName: string;
  originalMessageId?: string;
  additionalMembers?: string[];
  config?: RequirementFollowConfig;
}): Promise<StartWorkflowResult> {
  const config = params.config || getDefaultConfig();
  if (!config) return { success: false, error: '无法加载飞书配置' };
  
  const workflow = new RequirementFollowWorkflow(config);
  return workflow.startWorkflow(params);
}

export async function completeRequirementFollow(requirementId: string, chatContext?: string, config?: RequirementFollowConfig): Promise<CompleteWorkflowResult> {
  const cfg = config || getDefaultConfig();
  if (!cfg) return { success: false, error: '无法加载飞书配置' };
  
  const workflow = new RequirementFollowWorkflow(cfg);
  return workflow.completeWorkflow(requirementId, chatContext);
}

export default RequirementFollowWorkflow;

// ==================== Skill 入口处理 ====================

interface SkillParams {
  requirementContent: string;
  requesterName: string;
  requesterId: string;
  sourceChatId: string;
  sourceChatName: string;
  originalMessageId?: string;
}

interface DaemonParams {
  mode: 'daemon';
  pollInterval?: number;
}

/**
 * 解析命令行参数
 */
function parseCommandLineArgs(): SkillParams | DaemonParams | null {
  const args = process.argv.slice(2);
  
  // 检查是否是守护进程模式
  if (args.includes('--daemon') || args.includes('-d')) {
    const daemonParams: DaemonParams = { mode: 'daemon' };
    const intervalIndex = args.findIndex(arg => arg === '--interval' || arg === '-i');
    if (intervalIndex !== -1 && args[intervalIndex + 1]) {
      daemonParams.pollInterval = parseInt(args[intervalIndex + 1], 10);
    }
    return daemonParams;
  }
  
  const params: Partial<SkillParams> = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--content':
      case '-c':
        params.requirementContent = args[++i];
        break;
      case '--requester':
      case '-r':
        params.requesterName = args[++i];
        break;
      case '--requester-id':
      case '-rid':
        params.requesterId = args[++i];
        break;
      case '--chat-id':
      case '-cid':
        params.sourceChatId = args[++i];
        break;
      case '--chat-name':
      case '-cn':
        params.sourceChatName = args[++i];
        break;
      case '--message-id':
      case '-mid':
        params.originalMessageId = args[++i];
        break;
      case '--json':
      case '-j':
        try {
          const jsonData = JSON.parse(args[++i]);
          Object.assign(params, jsonData);
        } catch (e) {
          console.error('❌ 解析 JSON 参数失败:', e);
          return null;
        }
        break;
    }
  }

  // 验证必需参数
  if (!params.requirementContent || !params.requesterName || !params.requesterId || !params.sourceChatId || !params.sourceChatName) {
    console.error('❌ 缺少必需参数');
    printUsage();
    return null;
  }

  return params as SkillParams;
}

/**
 * 打印使用说明
 */
function printUsage(): void {
  console.log('用法:');
  console.log('  node dist/index.js [选项]');
  console.log('');
  console.log('工作流模式选项:');
  console.log('  --content, -c       需求内容');
  console.log('  --requester, -r     需求方姓名');
  console.log('  --requester-id, -rid 需求方OpenID');
  console.log('  --chat-id, -cid     来源群ID');
  console.log('  --chat-name, -cn    来源群名称');
  console.log('  --message-id, -mid  原始消息ID');
  console.log('  --json, -j          JSON格式参数');
  console.log('');
  console.log('守护进程模式选项:');
  console.log('  --daemon, -d        启动消息轮询守护进程');
  console.log('  --interval, -i      轮询间隔（毫秒，默认5000）');
  console.log('');
  console.log('示例:');
  console.log('  # 启动工作流');
  console.log('  node dist/index.js -c "需求内容" -r "张三" -rid "ou_xxx" -cid "oc_xxx" -cn "测试群"');
  console.log('');
  console.log('  # 启动守护进程');
  console.log('  node dist/index.js --daemon');
  console.log('  node dist/index.js --daemon --interval 3000');
  console.log('');
  console.log('  # JSON参数');
  console.log('  node dist/index.js --json \'{"requirementContent":"需求","requesterName":"张三",...}\'');
}

/**
 * 从 stdin 读取参数（用于被其他 skill 调用时）
 */
async function readStdinParams(): Promise<SkillParams | DaemonParams | null> {
  return new Promise((resolve) => {
    let data = '';

    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });

    process.stdin.on('end', () => {
      if (!data.trim()) {
        resolve(null);
        return;
      }

      try {
        const params = JSON.parse(data.trim()) as SkillParams;
        // 验证必需参数
        if (!params.requirementContent || !params.requesterName || !params.requesterId || !params.sourceChatId || !params.sourceChatName) {
          console.error('❌ 从 stdin 读取的参数缺少必需字段');
          resolve(null);
          return;
        }
        resolve(params);
      } catch (e) {
        console.error('❌ 解析 stdin JSON 参数失败:', e);
        resolve(null);
      }
    });

    // 如果没有 stdin 输入，100ms后返回 null
    setTimeout(() => {
      if (!data) {
        resolve(null);
      }
    }, 100);
  });
}

/**
 * 运行守护进程模式
 */
async function runDaemonMode(pollInterval: number = 5000): Promise<void> {
  console.log('='.repeat(60));
  console.log('🔔 Requirement Follow 消息轮询守护进程');
  console.log('='.repeat(60));
  console.log(`轮询间隔: ${pollInterval}ms`);
  console.log('按 Ctrl+C 停止...\n');

  const config = getDefaultConfig();
  if (!config) {
    console.error('❌ 无法加载飞书配置');
    process.exit(1);
  }

  const api = new FeishuAPI({ appId: config.appId, appSecret: config.appSecret });
  
  // 显示当前活跃会话
  const activeSessions = getActiveResearchSessions();
  console.log(`发现 ${activeSessions.length} 个活跃调研会话:`);
  for (const session of activeSessions) {
    console.log(`  - [${session.chat_id}] ${session.requirement_title} (${session.status})`);
  }
  console.log('');

  // 启动全局轮询
  const polling = startResearchPolling(api, {
    intervalMs: pollInterval,
    onMessage: (chatId, result) => {
      const timestamp = new Date().toISOString();
      if (result.result?.action === 'completed') {
        console.log(`[${timestamp}] [${chatId}] ✅ 调研完成`);
      } else if (result.result?.action === 'cancelled') {
        console.log(`[${timestamp}] [${chatId}] ❌ 调研已取消`);
      } else if (result.result?.action === 'next_question') {
        console.log(`[${timestamp}] [${chatId}] ➡️ 进入下一个问题`);
      } else {
        console.log(`[${timestamp}] [${chatId}] 💬 消息已处理: ${result.result?.action || 'unknown'}`);
      }
    },
    onError: (chatId, error) => {
      console.error(`[${new Date().toISOString()}] [${chatId}] ❌ 错误:`, error.message);
    }
  });

  // 处理退出信号
  process.on('SIGINT', () => {
    console.log('\n🛑 正在停止守护进程...');
    polling.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\n🛑 正在停止守护进程...');
    polling.stop();
    process.exit(0);
  });

  // 保持进程运行
  await new Promise(() => {});
}

/**
 * Skill 入口函数
 */
async function main(): Promise<void> {
  console.log('='.repeat(60));
  console.log('🎯 Requirement Follow Skill 启动');
  console.log('='.repeat(60));

  const params = parseCommandLineArgs();

  if (!params) {
    console.error('❌ 无法获取启动参数');
    process.exit(1);
  }

  // 检查是否是守护进程模式
  if ('mode' in params && params.mode === 'daemon') {
    await runDaemonMode(params.pollInterval);
    return;
  }

  // 工作流模式
  const workflowParams = params as SkillParams;
  
  console.log('  📋 参数:');
  console.log(`    需求内容: ${workflowParams.requirementContent.slice(0, 50)}...`);
  console.log(`    需求方: ${workflowParams.requesterName}`);
  console.log(`    来源群: ${workflowParams.sourceChatName}`);

  // 启动工作流
  const result = await startRequirementFollow({
    requirementContent: workflowParams.requirementContent,
    requesterName: workflowParams.requesterName,
    requesterId: workflowParams.requesterId,
    sourceChatId: workflowParams.sourceChatId,
    sourceChatName: workflowParams.sourceChatName,
    originalMessageId: workflowParams.originalMessageId
  });

  if (result.success) {
    console.log('✅ 工作流启动成功');
    if (result.isDuplicate) {
      console.log(`⚠️ 发现重复需求: ${result.existingRecordId}`);
    } else {
      console.log(`📝 记录ID: ${result.recordId}`);
      console.log(`💬 调研群: ${result.chatName} (${result.chatId})`);
    }
    process.exit(0);
  } else {
    console.error('❌ 工作流启动失败:', result.error);
    process.exit(1);
  }
}

// 如果直接运行此文件，执行 main 函数
if (require.main === module) {
  main().catch((error) => {
    console.error('❌ 未捕获的错误:', error);
    process.exit(1);
  });
}

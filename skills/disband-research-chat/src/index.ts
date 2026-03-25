#!/usr/bin/env node

import { ConfigManager, ErrorCode, ErrorMessages } from './config';
import Logger, { LogLevel } from './logger';
import FeishuAPI from './feishu-api';

/**
 * 命令行参数接口
 */
interface CLIArgs {
  chatId?: string;
  verbose: boolean;
  dryRun: boolean;
  help: boolean;
}

/**
 * 解析命令行参数
 */
function parseArgs(): CLIArgs {
  const args = process.argv.slice(2);
  const result: CLIArgs = {
    verbose: false,
    dryRun: false,
    help: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--chat-id':
      case '-c':
        result.chatId = args[++i];
        break;
      case '--verbose':
      case '-v':
        result.verbose = true;
        break;
      case '--dry-run':
      case '-d':
        result.dryRun = true;
        break;
      case '--help':
      case '-h':
        result.help = true;
        break;
      default:
        if (!arg.startsWith('-') && !result.chatId) {
          result.chatId = arg;
        }
        break;
    }
  }

  // 检查环境变量
  if (!result.chatId && process.env.DISBAND_CHAT_ID) {
    result.chatId = process.env.DISBAND_CHAT_ID;
  }

  return result;
}

/**
 * 显示帮助信息
 */
function showHelp(): void {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║           飞书调研群解散工具 (Disband Research Chat)          ║
╚══════════════════════════════════════════════════════════════╝

用法:
  disband-research-chat [选项] [群ID]

选项:
  -c, --chat-id <id>    指定要解散的群ID
  -v, --verbose         显示详细日志
  -d, --dry-run         模拟运行，不实际解散群组
  -h, --help            显示帮助信息

调用方式:
  1. 命令行参数: disband-research-chat --chat-id oc_xxx
  2. 环境变量:   DISBAND_CHAT_ID=oc_xxx disband-research-chat
  3. 位置参数:   disband-research-chat oc_xxx
  4. 交互式:     disband-research-chat (会提示输入群ID)

配置:
  工具会从 ~/.openclaw/openclaw.json 读取飞书凭证
  需要包含: app_id 和 app_secret

示例:
  disband-research-chat --chat-id oc_1234567890abcdef1234567890abcdef
  disband-research-chat -c oc_xxx -v
  DISBAND_CHAT_ID=oc_xxx disband-research-chat --verbose
`);
}

/**
 * 交互式输入
 */
function prompt(question: string): Promise<string> {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(question, (answer: string) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

/**
 * 格式化结果输出
 */
function formatResult(success: boolean, message: string, details?: Record<string, any>): void {
  if (success) {
    console.log('\n✅ ' + message);
  } else {
    console.log('\n❌ ' + message);
  }
  
  if (details) {
    Object.entries(details).forEach(([key, value]) => {
      console.log(`   ${key}: ${value}`);
    });
  }
}

/**
 * 主函数
 */
async function main(): Promise<void> {
  const args = parseArgs();

  // 显示帮助
  if (args.help) {
    showHelp();
    process.exit(0);
  }

  // 初始化配置管理器
  const configManager = new ConfigManager();
  
  // 初始化日志
  const logger = new Logger(
    undefined, 
    args.verbose ? LogLevel.DEBUG : LogLevel.INFO
  );

  logger.logOperation('START', {
    dryRun: args.dryRun,
    verbose: args.verbose
  });

  try {
    // 加载配置
    console.log('📋 正在加载配置...');
    const config = configManager.loadConfig();
    logger.debug('Config loaded', { appId: config.credentials.app_id });

    // 获取群ID
    let chatId = args.chatId;
    
    if (!chatId) {
      // 交互式输入
      console.log('\n未检测到群ID，请输入:');
      chatId = await prompt('群ID (格式: oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx): ');
      
      if (!chatId) {
        formatResult(false, ErrorMessages[ErrorCode.CHAT_ID_MISSING]);
        logger.error('Chat ID missing');
        process.exit(ErrorCode.CHAT_ID_MISSING);
      }
    }

    // 验证群ID格式
    console.log(`\n🔍 验证群ID: ${chatId}`);
    logger.info('Validating chat ID', { chatId });

    if (!configManager.validateChatId(chatId)) {
      const errorMsg = `${ErrorMessages[ErrorCode.CHAT_ID_INVALID]}\n   正确格式: oc_ + 32位十六进制字符`;
      formatResult(false, errorMsg);
      logger.error('Invalid chat ID format', { chatId });
      process.exit(ErrorCode.CHAT_ID_INVALID);
    }

    // 初始化飞书API客户端
    console.log('🔗 连接飞书API...');
    const feishu = new FeishuAPI(config.credentials, logger);
    
    // 获取访问令牌（验证凭证有效性）
    await feishu.getTenantAccessToken();
    console.log('✓ 认证成功\n');

    // 模拟运行模式
    if (args.dryRun) {
      console.log('🧪 [模拟运行模式] 不会实际解散群组');
      logger.logOperation('DRY_RUN', { chatId });
      
      // 验证群是否存在
      const chatInfo = await feishu.getChatInfo(chatId);
      if (chatInfo.code === 0) {
        formatResult(true, '模拟解散成功', {
          chatId,
          status: '群组存在，可以解散'
        });
      } else if (chatInfo.code === 230004) {
        formatResult(false, '模拟解散失败', {
          chatId,
          status: '群组不存在或已被解散'
        });
      } else {
        formatResult(false, '模拟解散失败', {
          chatId,
          error: chatInfo.msg,
          code: chatInfo.code
        });
      }
      logger.logOperation('DRY_RUN_COMPLETE', { chatId, code: chatInfo.code });
      process.exit(0);
    }

    // 确认操作
    console.log('⚠️  警告: 此操作将永久解散群组，不可恢复！');
    const confirmText = await prompt(`请输入 "DISBAND ${chatId}" 以确认解散: `);
    
    if (confirmText !== `DISBAND ${chatId}`) {
      formatResult(false, '操作已取消');
      logger.logOperation('CANCELLED', { chatId, reason: 'confirmation_failed' });
      process.exit(0);
    }

    // 执行解散操作
    console.log('\n🗑️  正在解散群组...');
    logger.logOperation('DISBANDING', { chatId });

    const startTime = Date.now();
    const result = await feishu.disbandChat(chatId);
    const duration = Date.now() - startTime;

    // 输出结果
    formatResult(true, '群组解散成功！', {
      chatId,
      duration: `${duration}ms`,
      code: result.code
    });

    logger.logOperation('SUCCESS', {
      chatId,
      duration,
      code: result.code
    });

    process.exit(0);

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    // 解析错误码
    let exitCode = ErrorCode.UNKNOWN_ERROR;
    
    if (errorMessage.includes('CONFIG_NOT_FOUND')) {
      exitCode = ErrorCode.CONFIG_NOT_FOUND;
    } else if (errorMessage.includes('CREDENTIALS_INVALID') || errorMessage.includes('app_id')) {
      exitCode = ErrorCode.CREDENTIALS_INVALID;
    } else if (errorMessage.includes('Token error')) {
      exitCode = ErrorCode.TOKEN_ERROR;
    } else if (errorMessage.includes('权限不足')) {
      exitCode = ErrorCode.PERMISSION_DENIED;
    } else if (errorMessage.includes('API Error')) {
      exitCode = ErrorCode.API_ERROR;
    } else if (errorMessage.includes('network') || errorMessage.includes('timeout')) {
      exitCode = ErrorCode.NETWORK_ERROR;
    }

    formatResult(false, errorMessage);
    
    logger.error('Operation failed', {
      error: errorMessage,
      exitCode
    });

    // 显示帮助提示
    if (exitCode === ErrorCode.CONFIG_NOT_FOUND || exitCode === ErrorCode.CREDENTIALS_INVALID) {
      console.log('\n💡 提示: 请确保 ~/.openclaw/openclaw.json 文件存在且包含有效的飞书凭证');
      console.log('   格式: { "app_id": "cli_xxx", "app_secret": "xxx" }');
    }

    process.exit(exitCode);
  }
}

// 运行主程序
main().catch((error) => {
  console.error('未处理的错误:', error);
  process.exit(ErrorCode.UNKNOWN_ERROR);
});

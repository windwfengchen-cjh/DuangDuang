#!/usr/bin/env node
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const config_1 = require("./config");
const logger_1 = __importStar(require("./logger"));
const feishu_api_1 = __importDefault(require("./feishu-api"));
/**
 * 解析命令行参数
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const result = {
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
function showHelp() {
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
function prompt(question) {
    const readline = require('readline');
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            rl.close();
            resolve(answer.trim());
        });
    });
}
/**
 * 格式化结果输出
 */
function formatResult(success, message, details) {
    if (success) {
        console.log('\n✅ ' + message);
    }
    else {
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
async function main() {
    const args = parseArgs();
    // 显示帮助
    if (args.help) {
        showHelp();
        process.exit(0);
    }
    // 初始化配置管理器
    const configManager = new config_1.ConfigManager();
    // 初始化日志
    const logger = new logger_1.default(undefined, args.verbose ? logger_1.LogLevel.DEBUG : logger_1.LogLevel.INFO);
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
                formatResult(false, config_1.ErrorMessages[config_1.ErrorCode.CHAT_ID_MISSING]);
                logger.error('Chat ID missing');
                process.exit(config_1.ErrorCode.CHAT_ID_MISSING);
            }
        }
        // 验证群ID格式
        console.log(`\n🔍 验证群ID: ${chatId}`);
        logger.info('Validating chat ID', { chatId });
        if (!configManager.validateChatId(chatId)) {
            const errorMsg = `${config_1.ErrorMessages[config_1.ErrorCode.CHAT_ID_INVALID]}\n   正确格式: oc_ + 32位十六进制字符`;
            formatResult(false, errorMsg);
            logger.error('Invalid chat ID format', { chatId });
            process.exit(config_1.ErrorCode.CHAT_ID_INVALID);
        }
        // 初始化飞书API客户端
        console.log('🔗 连接飞书API...');
        const feishu = new feishu_api_1.default(config.credentials, logger);
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
            }
            else if (chatInfo.code === 230004) {
                formatResult(false, '模拟解散失败', {
                    chatId,
                    status: '群组不存在或已被解散'
                });
            }
            else {
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
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        // 解析错误码
        let exitCode = config_1.ErrorCode.UNKNOWN_ERROR;
        if (errorMessage.includes('CONFIG_NOT_FOUND')) {
            exitCode = config_1.ErrorCode.CONFIG_NOT_FOUND;
        }
        else if (errorMessage.includes('CREDENTIALS_INVALID') || errorMessage.includes('app_id')) {
            exitCode = config_1.ErrorCode.CREDENTIALS_INVALID;
        }
        else if (errorMessage.includes('Token error')) {
            exitCode = config_1.ErrorCode.TOKEN_ERROR;
        }
        else if (errorMessage.includes('权限不足')) {
            exitCode = config_1.ErrorCode.PERMISSION_DENIED;
        }
        else if (errorMessage.includes('API Error')) {
            exitCode = config_1.ErrorCode.API_ERROR;
        }
        else if (errorMessage.includes('network') || errorMessage.includes('timeout')) {
            exitCode = config_1.ErrorCode.NETWORK_ERROR;
        }
        formatResult(false, errorMessage);
        logger.error('Operation failed', {
            error: errorMessage,
            exitCode
        });
        // 显示帮助提示
        if (exitCode === config_1.ErrorCode.CONFIG_NOT_FOUND || exitCode === config_1.ErrorCode.CREDENTIALS_INVALID) {
            console.log('\n💡 提示: 请确保 ~/.openclaw/openclaw.json 文件存在且包含有效的飞书凭证');
            console.log('   格式: { "app_id": "cli_xxx", "app_secret": "xxx" }');
        }
        process.exit(exitCode);
    }
}
// 运行主程序
main().catch((error) => {
    console.error('未处理的错误:', error);
    process.exit(config_1.ErrorCode.UNKNOWN_ERROR);
});
//# sourceMappingURL=index.js.map
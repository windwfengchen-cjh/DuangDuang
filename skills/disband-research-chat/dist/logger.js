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
exports.Logger = exports.LogLevel = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
/**
 * 日志级别
 */
var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["DEBUG"] = 0] = "DEBUG";
    LogLevel[LogLevel["INFO"] = 1] = "INFO";
    LogLevel[LogLevel["WARN"] = 2] = "WARN";
    LogLevel[LogLevel["ERROR"] = 3] = "ERROR";
})(LogLevel || (exports.LogLevel = LogLevel = {}));
/**
 * 日志管理器类
 */
class Logger {
    constructor(logPath, level = LogLevel.INFO) {
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.logPath = logPath || path.join(os.homedir(), '.openclaw', 'logs', 'disband-research-chat.log');
        this.level = level;
        this.ensureLogDir();
    }
    /**
     * 确保日志目录存在
     */
    ensureLogDir() {
        const logDir = path.dirname(this.logPath);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }
    /**
     * 获取当前时间戳
     */
    getTimestamp() {
        return new Date().toISOString();
    }
    /**
     * 格式化日志消息
     */
    format(level, message, meta) {
        const timestamp = this.getTimestamp();
        const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
        return `[${timestamp}] [${level}] ${message}${metaStr}\n`;
    }
    /**
     * 写入日志文件
     */
    write(level, message, meta) {
        if (this.level > this.getLogLevelFromString(level))
            return;
        const logEntry = this.format(level, message, meta);
        try {
            // 检查文件大小，如果超过限制则轮转
            if (fs.existsSync(this.logPath)) {
                const stats = fs.statSync(this.logPath);
                if (stats.size > this.maxFileSize) {
                    this.rotateLog();
                }
            }
            fs.appendFileSync(this.logPath, logEntry, 'utf-8');
        }
        catch (error) {
            console.error('Failed to write log:', error);
        }
    }
    /**
     * 从字符串获取日志级别
     */
    getLogLevelFromString(level) {
        switch (level) {
            case 'DEBUG': return LogLevel.DEBUG;
            case 'INFO': return LogLevel.INFO;
            case 'WARN': return LogLevel.WARN;
            case 'ERROR': return LogLevel.ERROR;
            default: return LogLevel.INFO;
        }
    }
    /**
     * 轮转日志文件
     */
    rotateLog() {
        try {
            const backupPath = `${this.logPath}.old`;
            if (fs.existsSync(backupPath)) {
                fs.unlinkSync(backupPath);
            }
            fs.renameSync(this.logPath, backupPath);
        }
        catch (error) {
            console.error('Failed to rotate log:', error);
        }
    }
    /**
     * 调试日志
     */
    debug(message, meta) {
        this.write('DEBUG', message, meta);
    }
    /**
     * 信息日志
     */
    info(message, meta) {
        this.write('INFO', message, meta);
    }
    /**
     * 警告日志
     */
    warn(message, meta) {
        this.write('WARN', message, meta);
    }
    /**
     * 错误日志
     */
    error(message, meta) {
        this.write('ERROR', message, meta);
    }
    /**
     * 记录操作日志
     */
    logOperation(operation, details) {
        this.info(`OPERATION: ${operation}`, details);
    }
    /**
     * 获取日志文件路径
     */
    getLogPath() {
        return this.logPath;
    }
}
exports.Logger = Logger;
exports.default = Logger;
//# sourceMappingURL=logger.js.map
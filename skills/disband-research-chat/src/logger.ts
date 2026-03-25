import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * 日志级别
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

/**
 * 日志管理器类
 */
export class Logger {
  private logPath: string;
  private level: LogLevel;
  private maxFileSize: number = 10 * 1024 * 1024; // 10MB

  constructor(logPath?: string, level: LogLevel = LogLevel.INFO) {
    this.logPath = logPath || path.join(os.homedir(), '.openclaw', 'logs', 'disband-research-chat.log');
    this.level = level;
    this.ensureLogDir();
  }

  /**
   * 确保日志目录存在
   */
  private ensureLogDir(): void {
    const logDir = path.dirname(this.logPath);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  /**
   * 获取当前时间戳
   */
  private getTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * 格式化日志消息
   */
  private format(level: string, message: string, meta?: Record<string, any>): string {
    const timestamp = this.getTimestamp();
    const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
    return `[${timestamp}] [${level}] ${message}${metaStr}\n`;
  }

  /**
   * 写入日志文件
   */
  private write(level: string, message: string, meta?: Record<string, any>): void {
    if (this.level > this.getLogLevelFromString(level)) return;

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
    } catch (error) {
      console.error('Failed to write log:', error);
    }
  }

  /**
   * 从字符串获取日志级别
   */
  private getLogLevelFromString(level: string): LogLevel {
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
  private rotateLog(): void {
    try {
      const backupPath = `${this.logPath}.old`;
      if (fs.existsSync(backupPath)) {
        fs.unlinkSync(backupPath);
      }
      fs.renameSync(this.logPath, backupPath);
    } catch (error) {
      console.error('Failed to rotate log:', error);
    }
  }

  /**
   * 调试日志
   */
  debug(message: string, meta?: Record<string, any>): void {
    this.write('DEBUG', message, meta);
  }

  /**
   * 信息日志
   */
  info(message: string, meta?: Record<string, any>): void {
    this.write('INFO', message, meta);
  }

  /**
   * 警告日志
   */
  warn(message: string, meta?: Record<string, any>): void {
    this.write('WARN', message, meta);
  }

  /**
   * 错误日志
   */
  error(message: string, meta?: Record<string, any>): void {
    this.write('ERROR', message, meta);
  }

  /**
   * 记录操作日志
   */
  logOperation(operation: string, details: Record<string, any>): void {
    this.info(`OPERATION: ${operation}`, details);
  }

  /**
   * 获取日志文件路径
   */
  getLogPath(): string {
    return this.logPath;
  }
}

export default Logger;

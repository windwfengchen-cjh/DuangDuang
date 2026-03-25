/**
 * 日志级别
 */
export declare enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}
/**
 * 日志管理器类
 */
export declare class Logger {
    private logPath;
    private level;
    private maxFileSize;
    constructor(logPath?: string, level?: LogLevel);
    /**
     * 确保日志目录存在
     */
    private ensureLogDir;
    /**
     * 获取当前时间戳
     */
    private getTimestamp;
    /**
     * 格式化日志消息
     */
    private format;
    /**
     * 写入日志文件
     */
    private write;
    /**
     * 从字符串获取日志级别
     */
    private getLogLevelFromString;
    /**
     * 轮转日志文件
     */
    private rotateLog;
    /**
     * 调试日志
     */
    debug(message: string, meta?: Record<string, any>): void;
    /**
     * 信息日志
     */
    info(message: string, meta?: Record<string, any>): void;
    /**
     * 警告日志
     */
    warn(message: string, meta?: Record<string, any>): void;
    /**
     * 错误日志
     */
    error(message: string, meta?: Record<string, any>): void;
    /**
     * 记录操作日志
     */
    logOperation(operation: string, details: Record<string, any>): void;
    /**
     * 获取日志文件路径
     */
    getLogPath(): string;
}
export default Logger;
//# sourceMappingURL=logger.d.ts.map
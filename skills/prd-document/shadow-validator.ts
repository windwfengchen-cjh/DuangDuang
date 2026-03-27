/**
 * 影子验证器 - PRD Document Skill
 * 
 * 用途：在不影响现有逻辑的情况下，验证元数据匹配规则的准确性
 * 通过对比旧逻辑结果和元数据匹配结果，收集数据以优化触发机制
 */

import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

const readFile = promisify(fs.readFile);
const appendFile = promisify(fs.appendFile);
const mkdir = promisify(fs.mkdir);

// 影子日志条目接口
interface ShadowLog {
  timestamp: string;
  message: string;
  oldLogicResult: string;
  metadataMatch: boolean;
  triggerWord: string | null;
  match: boolean;
}

// 技能元数据接口
interface SkillMetadata {
  name: string;
  alias?: string[];
  description?: string;
  keywords?: string[];
  trigger?: string[];
  version?: string;
  category?: string;
}

// 旧逻辑结果接口
interface OldLogicResult {
  skill: string | null;
  confidence?: number;
  [key: string]: any;
}

/**
 * 影子验证器类
 * 用于并行验证元数据匹配规则，不影响主流程
 */
export class ShadowValidator {
  private logFile: string;
  private skillPath: string;
  private metadata: SkillMetadata | null = null;

  constructor(
    logFile: string = '~/logs/shadow-validation/prd-document.jsonl',
    skillPath: string = '~/openclaw/workspace/skills/prd-document/SKILL.md'
  ) {
    // 展开 home 目录
    this.logFile = logFile.replace(/^~/, process.env.HOME || '');
    this.skillPath = skillPath.replace(/^~/, process.env.HOME || '');
  }

  /**
   * 确保日志目录存在
   */
  private async ensureLogDirectory(): Promise<void> {
    const dir = path.dirname(this.logFile);
    try {
      await mkdir(dir, { recursive: true });
    } catch (err) {
      // 目录已存在则忽略
    }
  }

  /**
   * 从 SKILL.md 读取元数据
   */
  async loadMetadata(): Promise<SkillMetadata> {
    if (this.metadata) {
      return this.metadata;
    }

    try {
      const skillContent = await readFile(this.skillPath, 'utf-8');
      this.metadata = this.parseFrontmatter(skillContent);
      return this.metadata;
    } catch (error) {
      console.error('[ShadowValidator] 读取 SKILL.md 失败:', error);
      // 返回默认元数据
      return {
        name: 'prd-document',
        trigger: ['写PRD', '创建PRD', '产品需求文档', '需求文档', 'PRD文档']
      };
    }
  }

  /**
   * 解析 Markdown 前置元数据
   */
  private parseFrontmatter(content: string): SkillMetadata {
    const frontmatterMatch = content.match(/^---\s*\n([\s\S]*?)\n---/);
    
    if (!frontmatterMatch) {
      throw new Error('SKILL.md 中没有找到前置元数据');
    }

    const frontmatter = frontmatterMatch[1];
    const metadata: SkillMetadata = { name: 'prd-document' };

    // 解析各字段
    const nameMatch = frontmatter.match(/name:\s*(.+)/);
    if (nameMatch) metadata.name = nameMatch[1].trim();

    const aliasMatch = frontmatter.match(/alias:\s*\[(.*?)\]/);
    if (aliasMatch) {
      metadata.alias = aliasMatch[1].split(',').map(s => s.trim().replace(/['"]/g, ''));
    }

    const descriptionMatch = frontmatter.match(/description:\s*(.+)/);
    if (descriptionMatch) metadata.description = descriptionMatch[1].trim();

    const keywordsMatch = frontmatter.match(/keywords:\s*\[(.*?)\]/);
    if (keywordsMatch) {
      metadata.keywords = keywordsMatch[1].split(',').map(s => s.trim().replace(/['"]/g, ''));
    }

    const triggerMatch = frontmatter.match(/trigger:\s*\[(.*?)\]/s);
    if (triggerMatch) {
      metadata.trigger = triggerMatch[1]
        .split(',')
        .map(s => s.trim().replace(/['"]/g, ''))
        .filter(s => s.length > 0);
    }

    const versionMatch = frontmatter.match(/version:\s*["']?(.+?)["']?\s*$/m);
    if (versionMatch) metadata.version = versionMatch[1].trim();

    const categoryMatch = frontmatter.match(/category:\s*(.+)/);
    if (categoryMatch) metadata.category = categoryMatch[1].trim();

    return metadata;
  }

  /**
   * 检查元数据触发词匹配
   */
  checkMetadataMatch(
    text: string,
    metadata: SkillMetadata
  ): { matched: boolean; triggerWord: string | null } {
    if (!metadata.trigger || metadata.trigger.length === 0) {
      return { matched: false, triggerWord: null };
    }

    for (const trigger of metadata.trigger) {
      if (text.includes(trigger)) {
        return { matched: true, triggerWord: trigger };
      }
    }

    return { matched: false, triggerWord: null };
  }

  /**
   * 执行完整的影子验证
   * @param text 输入消息文本
   * @param oldLogicFn 旧逻辑处理函数
   * @returns 旧逻辑结果（保持不变）
   */
  async validate<T extends OldLogicResult>(
    text: string,
    oldLogicFn: (text: string) => T | Promise<T>
  ): Promise<T> {
    // 执行旧逻辑
    const oldResult = await Promise.resolve(oldLogicFn(text));

    // 执行影子验证（不阻塞主流程）
    this.performShadowValidation(text, oldResult).catch(err => {
      console.error('[ShadowValidator] 影子验证失败:', err);
    });

    // 始终返回旧逻辑结果
    return oldResult;
  }

  /**
   * 执行影子验证（内部方法）
   */
  private async performShadowValidation(
    text: string,
    oldResult: OldLogicResult
  ): Promise<void> {
    const metadata = await this.loadMetadata();
    const metadataCheck = this.checkMetadataMatch(text, metadata);

    const logEntry: ShadowLog = {
      timestamp: new Date().toISOString(),
      message: text,
      oldLogicResult: oldResult.skill || 'none',
      metadataMatch: metadataCheck.matched,
      triggerWord: metadataCheck.triggerWord,
      match: oldResult.skill === 'prd-document' && metadataCheck.matched
    };

    await this.logComparison(logEntry);
  }

  /**
   * 记录对比结果到日志文件
   */
  async logComparison(log: ShadowLog): Promise<void> {
    await this.ensureLogDirectory();
    const logLine = JSON.stringify(log) + '\n';
    await appendFile(this.logFile, logLine);
  }

  /**
   * 快速验证方法（用于直接调用）
   */
  async quickValidate(
    text: string,
    oldResult: OldLogicResult
  ): Promise<void> {
    return this.performShadowValidation(text, oldResult);
  }
}

// 导出单例实例
export const shadowValidator = new ShadowValidator();

// 默认导出
export default ShadowValidator;

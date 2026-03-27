#!/usr/bin/env node
/**
 * 影子验证日志分析脚本
 * 
 * 用法: npx ts-node analyze-shadow-logs.ts [options]
 * 
 * 选项:
 *   --log-file <path>    指定日志文件路径
 *   --output <format>    输出格式: text|json (默认: text)
 *   --days <number>      分析最近 N 天的数据
 *   --save-report        保存报告到文件
 */

import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

const readFile = promisify(fs.readFile);
const writeFile = promisify(fs.writeFile);

// 日志条目接口
interface ShadowLog {
  timestamp: string;
  message: string;
  oldLogicResult: string;
  metadataMatch: boolean;
  triggerWord: string | null;
  match: boolean;
}

// 分析报告接口
interface AnalysisReport {
  generatedAt: string;
  logFile: string;
  totalLogs: number;
  dateRange: {
    start: string;
    end: string;
  };
  matchRate: {
    overall: number;
    truePositives: number;
    falsePositives: number;
    falseNegatives: number;
    trueNegatives: number;
  };
  triggerWords: {
    word: string;
    count: number;
  }[];
  oldLogicDistribution: {
    skill: string;
    count: number;
  }[];
  mismatches: ShadowLog[];
  recommendations: string[];
}

/**
 * 读取并解析日志文件
 */
async function readLogs(logFile: string): Promise<ShadowLog[]> {
  try {
    const content = await readFile(logFile, 'utf-8');
    const lines = content.trim().split('\n').filter(line => line.length > 0);
    
    return lines.map(line => {
      try {
        return JSON.parse(line) as ShadowLog;
      } catch {
        return null;
      }
    }).filter((log): log is ShadowLog => log !== null);
  } catch (error) {
    console.error(`读取日志文件失败: ${logFile}`);
    return [];
  }
}

/**
 * 分析日志数据
 */
function analyzeLogs(logs: ShadowLog[]): AnalysisReport {
  const now = new Date();
  
  // 计算匹配率
  let truePositives = 0;  // 旧逻辑和元数据都匹配
  let falsePositives = 0; // 元数据匹配但旧逻辑不匹配
  let falseNegatives = 0; // 旧逻辑匹配但元数据不匹配
  let trueNegatives = 0;  // 两者都不匹配

  const triggerWordCounts = new Map<string, number>();
  const oldLogicCounts = new Map<string, number>();
  const mismatches: ShadowLog[] = [];

  for (const log of logs) {
    const oldMatched = log.oldLogicResult === 'prd-document';
    const metaMatched = log.metadataMatch;

    if (oldMatched && metaMatched) {
      truePositives++;
    } else if (!oldMatched && metaMatched) {
      falsePositives++;
      mismatches.push(log);
    } else if (oldMatched && !metaMatched) {
      falseNegatives++;
      mismatches.push(log);
    } else {
      trueNegatives++;
    }

    // 统计触发词
    if (log.triggerWord) {
      triggerWordCounts.set(
        log.triggerWord,
        (triggerWordCounts.get(log.triggerWord) || 0) + 1
      );
    }

    // 统计旧逻辑结果
    oldLogicCounts.set(
      log.oldLogicResult,
      (oldLogicCounts.get(log.oldLogicResult) || 0) + 1
    );
  }

  const total = logs.length;
  const matchRate = total > 0 ? ((truePositives + trueNegatives) / total) * 100 : 0;

  // 生成建议
  const recommendations: string[] = [];
  
  if (falsePositives > 0) {
    recommendations.push(`发现 ${falsePositives} 个假阳性案例（元数据匹配但旧逻辑不匹配），建议检查元数据触发词是否过于宽泛`);
  }
  
  if (falseNegatives > 0) {
    recommendations.push(`发现 ${falseNegatives} 个假阴性案例（旧逻辑匹配但元数据不匹配），建议更新元数据触发词`);
  }

  if (matchRate < 80) {
    recommendations.push(`整体匹配率 ${matchRate.toFixed(1)}% 较低，建议审查触发词配置`);
  }

  if (matchRate >= 95) {
    recommendations.push(`整体匹配率 ${matchRate.toFixed(1)}% 优秀，可以考虑将元数据匹配正式投入使用`);
  }

  // 触发词排序
  const sortedTriggers = Array.from(triggerWordCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([word, count]) => ({ word, count }));

  // 旧逻辑结果排序
  const sortedOldLogic = Array.from(oldLogicCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([skill, count]) => ({ skill, count }));

  return {
    generatedAt: now.toISOString(),
    logFile: '',
    totalLogs: total,
    dateRange: {
      start: logs.length > 0 ? logs[0].timestamp : now.toISOString(),
      end: logs.length > 0 ? logs[logs.length - 1].timestamp : now.toISOString()
    },
    matchRate: {
      overall: parseFloat(matchRate.toFixed(2)),
      truePositives,
      falsePositives,
      falseNegatives,
      trueNegatives
    },
    triggerWords: sortedTriggers,
    oldLogicDistribution: sortedOldLogic,
    mismatches: mismatches.slice(0, 20), // 只保留前20个不匹配案例
    recommendations
  };
}

/**
 * 生成文本格式报告
 */
function generateTextReport(report: AnalysisReport): string {
  const lines: string[] = [];

  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('           PRD Document 影子验证分析报告');
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('');
  lines.push(`📅 生成时间: ${report.generatedAt}`);
  lines.push(`📊 样本数量: ${report.totalLogs} 条`);
  lines.push(`📅 数据范围: ${report.dateRange.start} 至 ${report.dateRange.end}`);
  lines.push('');
  
  lines.push('─────────────────────────────────────────────────────────');
  lines.push('                    匹配率统计');
  lines.push('─────────────────────────────────────────────────────────');
  lines.push(`✅ 整体匹配率: ${report.matchRate.overall.toFixed(2)}%`);
  lines.push('');
  lines.push('混淆矩阵:');
  lines.push(`  真阳性 (TP): ${report.matchRate.truePositives}  旧逻辑和元数据都识别为 PRD`);
  lines.push(`  假阳性 (FP): ${report.matchRate.falsePositives}  元数据识别为 PRD 但旧逻辑未识别`);
  lines.push(`  假阴性 (FN): ${report.matchRate.falseNegatives}  旧逻辑识别为 PRD 但元数据未识别`);
  lines.push(`  真阴性 (TN): ${report.matchRate.trueNegatives}  两者都未识别为 PRD`);
  lines.push('');
  
  lines.push('─────────────────────────────────────────────────────────');
  lines.push('                    触发词统计');
  lines.push('─────────────────────────────────────────────────────────');
  if (report.triggerWords.length > 0) {
    report.triggerWords.forEach(({ word, count }) => {
      lines.push(`  "${word}": ${count} 次`);
    });
  } else {
    lines.push('  无触发词匹配记录');
  }
  lines.push('');
  
  lines.push('─────────────────────────────────────────────────────────');
  lines.push('                  旧逻辑结果分布');
  lines.push('─────────────────────────────────────────────────────────');
  report.oldLogicDistribution.forEach(({ skill, count }) => {
    const percentage = ((count / report.totalLogs) * 100).toFixed(1);
    lines.push(`  ${skill}: ${count} 次 (${percentage}%)`);
  });
  lines.push('');

  if (report.mismatches.length > 0) {
    lines.push('─────────────────────────────────────────────────────────');
    lines.push('                    不匹配案例 (前20条)');
    lines.push('─────────────────────────────────────────────────────────');
    report.mismatches.forEach((log, index) => {
      lines.push(`\n[${index + 1}] 时间: ${log.timestamp}`);
      lines.push(`    消息: ${log.message.substring(0, 100)}${log.message.length > 100 ? '...' : ''}`);
      lines.push(`    旧逻辑结果: ${log.oldLogicResult}`);
      lines.push(`    元数据匹配: ${log.metadataMatch ? '是' : '否'}`);
      lines.push(`    触发词: ${log.triggerWord || '无'}`);
    });
    lines.push('');
  }

  lines.push('─────────────────────────────────────────────────────────');
  lines.push('                      建议');
  lines.push('─────────────────────────────────────────────────────────');
  if (report.recommendations.length > 0) {
    report.recommendations.forEach((rec, index) => {
      lines.push(`${index + 1}. ${rec}`);
    });
  } else {
    lines.push('暂无建议');
  }
  lines.push('');
  lines.push('═══════════════════════════════════════════════════════════');

  return lines.join('\n');
}

/**
 * 主函数
 */
async function main(): Promise<void> {
  // 解析命令行参数
  const args = process.argv.slice(2);
  let logFile = path.join(process.env.HOME || '', 'logs/shadow-validation/prd-document.jsonl');
  let outputFormat: 'text' | 'json' = 'text';
  let saveReport = false;
  let days: number | null = null;

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--log-file':
        logFile = args[++i];
        break;
      case '--output':
        outputFormat = args[++i] as 'text' | 'json';
        break;
      case '--days':
        days = parseInt(args[++i], 10);
        break;
      case '--save-report':
        saveReport = true;
        break;
    }
  }

  // 读取日志
  console.log(`📖 读取日志文件: ${logFile}`);
  let logs = await readLogs(logFile);

  if (logs.length === 0) {
    console.log('⚠️  没有找到日志数据');
    process.exit(0);
  }

  // 按日期过滤
  if (days !== null) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    logs = logs.filter(log => new Date(log.timestamp) >= cutoffDate);
    console.log(`📅 过滤最近 ${days} 天的数据: ${logs.length} 条`);
  }

  // 分析数据
  console.log('🔍 分析数据中...');
  const report = analyzeLogs(logs);
  report.logFile = logFile;

  // 输出报告
  if (outputFormat === 'json') {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(generateTextReport(report));
  }

  // 保存报告
  if (saveReport) {
    const reportFile = logFile.replace('.jsonl', `-report-${Date.now()}.${outputFormat}`);
    const content = outputFormat === 'json' 
      ? JSON.stringify(report, null, 2)
      : generateTextReport(report);
    await writeFile(reportFile, content);
    console.log(`\n💾 报告已保存: ${reportFile}`);
  }
}

// 运行主函数
main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});

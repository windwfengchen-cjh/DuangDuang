/**
 * Feishu Feedback Handler - 影子验证集成示例
 * 
 * 此文件展示了如何在现有 feishu-feedback-handler 中集成影子验证
 * 实际使用时，请将相关代码合并到主 handler 文件中
 */

import { ShadowValidator } from './shadow-validator';

// 初始化影子验证器
const shadowValidator = new ShadowValidator();

/**
 * 旧的消息处理逻辑（保持不变）
 */
function handleMessageByOldLogic(text: string): { skill: string | null; confidence: number } {
  // 这里是现有的业务逻辑
  // 例如：基于关键词匹配、机器学习模型等
  
  // 示例实现
  const prdKeywords = ['PRD', '需求文档', '产品需求'];
  for (const keyword of prdKeywords) {
    if (text.includes(keyword)) {
      return { skill: 'prd-document', confidence: 0.8 };
    }
  }
  
  return { skill: null, confidence: 0 };
}

/**
 * 集成影子验证的消息处理函数
 */
async function handleMessageWithShadowValidation(text: string): Promise<{
  skill: string | null;
  confidence: number;
}> {
  // 1. 执行旧逻辑（保持不变）
  const oldResult = handleMessageByOldLogic(text);

  // 2. 执行影子验证（异步，不阻塞主流程）
  // 注意：这里不等待结果，确保不影响主流程性能
  shadowValidator.quickValidate(text, oldResult).catch(err => {
    console.error('[ShadowValidation] 验证失败:', err);
  });

  // 3. 仍返回旧逻辑结果
  return oldResult;
}

/**
 * 完整的 feishu 消息处理函数示例
 */
export async function handleFeishuMessage(message: {
  text: string;
  userId: string;
  chatId: string;
  messageId: string;
}): Promise<void> {
  const { text } = message;

  // 使用带影子验证的处理函数
  const result = await handleMessageWithShadowValidation(text);

  // 根据结果执行相应操作
  if (result.skill === 'prd-document') {
    console.log(`[Handler] 识别为 PRD 需求，置信度: ${result.confidence}`);
    // 执行 PRD 文档生成逻辑...
  } else {
    console.log('[Handler] 未识别为 PRD 需求');
    // 执行其他处理...
  }
}

/**
 * 批处理模式示例（用于历史数据分析）
 */
export async function batchAnalyzeWithShadow(messages: string[]): Promise<void> {
  console.log(`开始批量分析 ${messages.length} 条消息...`);

  const metadata = await shadowValidator.loadMetadata();

  for (const text of messages) {
    const oldResult = handleMessageByOldLogic(text);
    const metadataCheck = shadowValidator.checkMetadataMatch(text, metadata);

    await shadowValidator.logComparison({
      timestamp: new Date().toISOString(),
      message: text,
      oldLogicResult: oldResult.skill || 'none',
      metadataMatch: metadataCheck.matched,
      triggerWord: metadataCheck.triggerWord,
      match: oldResult.skill === 'prd-document' && metadataCheck.matched
    });
  }

  console.log('批量分析完成');
}

// 导出默认 handler
export default handleMessageWithShadowValidation;

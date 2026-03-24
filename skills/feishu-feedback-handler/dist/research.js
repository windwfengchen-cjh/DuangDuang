"use strict";
/**
 * 需求调研群消息处理器
 * 支持三种模式：
 * 1. 自动收集模式 - 收集群内所有消息（无需@）
 * 2. 问答模式 - 通过7个问题引导需求人回答
 * 3. 混合模式 - 问答+自动收集同时进行（推荐）
 *
 * 混合模式工作流程：
 * 1. 机器人发送7个问题引导需求人
 * 2. 同时自动收集群内所有成员的消息
 * 3. 识别需求人回答后自动发送下一个问题
 * 4. 所有消息（包括讨论）都保存到PRD
 */
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
exports.RESEARCH_QUESTIONS = void 0;
exports.formatQuestion = formatQuestion;
exports.loadResearchSession = loadResearchSession;
exports.saveResearchSession = saveResearchSession;
exports.deleteResearchSession = deleteResearchSession;
exports.loadChatMessages = loadChatMessages;
exports.saveChatMessages = saveChatMessages;
exports.addChatMessage = addChatMessage;
exports.createResearchSession = createResearchSession;
exports.isResearchChat = isResearchChat;
exports.isAutoCollectExpired = isAutoCollectExpired;
exports.startResearch = startResearch;
exports.handleResearchMessage = handleResearchMessage;
exports.getResearchStats = getResearchStats;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const utils_1 = require("./utils");
// 调研群状态存储路径
const RESEARCH_STATE_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research');
const RESEARCH_MESSAGES_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research_messages');
// 确保目录存在
if (!fs.existsSync(RESEARCH_STATE_DIR)) {
    fs.mkdirSync(RESEARCH_STATE_DIR, { recursive: true });
}
if (!fs.existsSync(RESEARCH_MESSAGES_DIR)) {
    fs.mkdirSync(RESEARCH_MESSAGES_DIR, { recursive: true });
}
/**
 * 调研问题定义 - 7个关键问题模板
 * 混合模式：问题用于引导需求人，同时收集所有群内消息
 */
exports.RESEARCH_QUESTIONS = [
    {
        key: 'background',
        question: '👋 大家好！需求调研现在开始。\n\n📋 **需求标题**: {title}\n👤 **需求人**: @{requester}\n\n🤖 我将通过 **7个关键问题** 引导调研，同时 **自动收集** 群内所有讨论内容。\n\n---\n\n**问题 1/7：业务背景**\n请描述一下这个需求的【业务背景】是什么？是在什么场景下产生的？\n\n💡 提示：为什么需要这个功能？要解决什么业务问题？',
        required: true,
        prd_section: '背景与目标'
    },
    {
        key: 'target_users',
        question: '**问题 2/7：目标用户**\n这个需求的【目标用户】是谁？\n\n💡 例如：内部同事（哪个部门/角色？）、外部客户、特定群体等',
        required: true,
        prd_section: '背景与目标'
    },
    {
        key: 'current_situation',
        question: '**问题 3/7：现状描述**\n请描述一下【当前的系统/流程现状】是什么样？\n\n💡 提示：用户现在是如何完成这个任务的？',
        required: true,
        prd_section: '现状'
    },
    {
        key: 'pain_points',
        question: '**问题 4/7：核心痛点**\n当前的【核心痛点】是什么？\n\n💡 提示：哪个步骤最耗时/容易出错？造成了什么影响？',
        required: true,
        prd_section: '现状'
    },
    {
        key: 'expected_solution',
        question: '**问题 5/7：期望解决方案**\n针对这个痛点，您【期望的解决方案】是什么？\n\n💡 提示：希望系统如何帮助用户？',
        required: true,
        prd_section: '方案'
    },
    {
        key: 'priority',
        question: '**问题 6/7：优先级和时间**\n请问这个需求的【优先级和时间要求】是怎样的？\n\n💡 例如：高/中/低，期望上线时间',
        required: true,
        prd_section: '优先级和时间计划'
    },
    {
        key: 'attachments',
        question: '**问题 7/7：相关资料**\n是否有相关的【数据、截图、文档】需要补充？如有请直接发送，没有请回复"无"。',
        required: false,
        prd_section: '附件与参考资料'
    }
];
/**
 * 获取格式化的问题文本（替换变量）
 */
function formatQuestion(questionTemplate, title, requesterName) {
    return questionTemplate
        .replace(/{title}/g, title)
        .replace(/{requester}/g, requesterName);
}
/**
 * 获取状态文件路径
 */
function getStateFilePath(chatId) {
    return path.join(RESEARCH_STATE_DIR, `${chatId}.json`);
}
/**
 * 获取消息存储文件路径
 */
function getMessagesFilePath(chatId) {
    return path.join(RESEARCH_MESSAGES_DIR, `${chatId}.json`);
}
/**
 * 加载调研会话状态
 */
function loadResearchSession(chatId) {
    const filePath = getStateFilePath(chatId);
    if (!fs.existsSync(filePath)) {
        return null;
    }
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(content);
    }
    catch (e) {
        console.error(`加载调研会话状态失败: ${chatId}`, e);
        return null;
    }
}
/**
 * 保存调研会话状态
 */
function saveResearchSession(session) {
    const filePath = getStateFilePath(session.chat_id);
    session.updated_at = new Date().toISOString();
    fs.writeFileSync(filePath, JSON.stringify(session, null, 2), 'utf-8');
}
/**
 * 删除调研会话状态
 */
function deleteResearchSession(chatId) {
    const filePath = getStateFilePath(chatId);
    if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
    }
    // 同时删除消息记录
    const messagesFilePath = getMessagesFilePath(chatId);
    if (fs.existsSync(messagesFilePath)) {
        fs.unlinkSync(messagesFilePath);
    }
}
/**
 * 加载群消息记录
 */
function loadChatMessages(chatId) {
    const filePath = getMessagesFilePath(chatId);
    if (!fs.existsSync(filePath)) {
        return [];
    }
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(content);
    }
    catch (e) {
        console.error(`加载群消息记录失败: ${chatId}`, e);
        return [];
    }
}
/**
 * 保存群消息记录
 */
function saveChatMessages(chatId, messages) {
    const filePath = getMessagesFilePath(chatId);
    fs.writeFileSync(filePath, JSON.stringify(messages, null, 2), 'utf-8');
}
/**
 * 添加消息到记录
 */
function addChatMessage(chatId, message) {
    const messages = loadChatMessages(chatId);
    // 检查是否已存在（去重）
    const exists = messages.some(m => m.message_id === message.message_id);
    if (!exists) {
        messages.push(message);
        saveChatMessages(chatId, messages);
    }
}
/**
 * 创建新的调研会话
 *
 * @param mode 调研模式: 'auto_collect' | 'qa' | 'hybrid' (默认hybrid)
 * @param autoCollectHours 自动收集时长（小时）
 */
function createResearchSession(chatId, requirementTitle, requirementPersonId, requirementPersonName, bossId, recordId, mode = 'hybrid', // 默认使用混合模式
autoCollectHours = 24 // 默认自动收集24小时
) {
    const now = new Date();
    const deadline = new Date(now.getTime() + autoCollectHours * 60 * 60 * 1000);
    // 根据模式设置标志位
    const isAutoCollect = mode === 'auto_collect' || mode === 'hybrid';
    const isQa = mode === 'qa' || mode === 'hybrid';
    const session = {
        chat_id: chatId,
        requirement_title: requirementTitle,
        requirement_person_id: requirementPersonId,
        requirement_person_name: requirementPersonName,
        boss_id: bossId,
        record_id: recordId,
        current_question_idx: 0,
        collected_data: {},
        attachments: [],
        status: 'waiting',
        created_at: now.toISOString(),
        updated_at: now.toISOString(),
        message_count: 0,
        // 模式配置
        mode: mode,
        auto_collect_mode: isAutoCollect, // 兼容旧字段
        // 混合模式配置
        enable_qa: isQa,
        enable_auto_collect: isAutoCollect,
        waiting_for_answer: isQa, // 如果启用问答，初始状态为等待回答
        // 自动收集配置
        auto_collect_deadline: deadline.toISOString(),
        processed_message_ids: []
    };
    saveResearchSession(session);
    console.log(`创建调研会话: mode=${mode}, enable_qa=${isQa}, enable_auto_collect=${isAutoCollect}`);
    return session;
}
/**
 * 检查是否是调研群
 */
function isResearchChat(chatId) {
    const session = loadResearchSession(chatId);
    return session !== null;
}
/**
 * 检查是否超出自动收集时间
 */
function isAutoCollectExpired(session) {
    if (!session.auto_collect_deadline) {
        return false;
    }
    const now = new Date();
    const deadline = new Date(session.auto_collect_deadline);
    return now > deadline;
}
/**
 * 启动调研（发送欢迎消息）
 */
async function startResearch(chatId, token) {
    const session = loadResearchSession(chatId);
    if (!session) {
        console.error(`调研会话不存在: ${chatId}`);
        return false;
    }
    // 发送欢迎消息
    const deadlineStr = session.auto_collect_deadline
        ? new Date(session.auto_collect_deadline).toLocaleString('zh-CN')
        : '24小时后';
    const welcomeMsg = session.auto_collect_mode
        ? `👋 大家好！需求调研群已创建。

📋 **需求标题**: ${session.requirement_title}
👤 **需求人**: ${session.requirement_person_name}

🤖 我将自动收集本群的所有消息（无需@我），用于生成PRD文档。

⏰ **自动收集截止时间**: ${deadlineStr}

💡 **提示**:
• 所有成员发送的消息都会被记录
• 请围绕需求主题进行讨论
• 发送「完成调研」可随时结束收集
• 发送「取消」可终止调研

开始收集需求信息... 🚀`
        : `👋 大家好！我是需求跟进助手。\n\n本群用于收集「**${session.requirement_title}**」的需求信息。\n\n我将通过7个关键问题来了解需求详情，请 **${session.requirement_person_name}** 配合回答。\n\n让我们开始吧！🚀`;
    await (0, utils_1.sendFeishuMessage)(chatId, welcomeMsg, token);
    if (session.auto_collect_mode) {
        // 自动收集模式：直接开始收集
        session.status = 'collecting';
        saveResearchSession(session);
        console.log(`调研已启动(自动收集模式): ${chatId}, 截止: ${deadlineStr}`);
    }
    else {
        // 问答模式：发送第一个问题
        const firstQuestion = exports.RESEARCH_QUESTIONS[0];
        await (0, utils_1.sendFeishuMessage)(chatId, firstQuestion.question, token);
        session.status = 'collecting';
        session.current_question_idx = 0;
        saveResearchSession(session);
        console.log(`调研已启动(问答模式): ${chatId}, 正在等待 ${session.requirement_person_name} 回答`);
    }
    return true;
}
/**
 * 提取文本内容
 */
function extractTextFromEvent(event) {
    let textContent = '';
    try {
        const content = JSON.parse(event.content);
        if (content.text) {
            textContent = content.text;
        }
        else if (content.post) {
            // 处理post类型消息
            const postContent = content.post.zh_cn || content.post;
            if (postContent) {
                if (postContent.title) {
                    textContent += postContent.title + '\n';
                }
                if (Array.isArray(postContent.content)) {
                    for (const block of postContent.content) {
                        if (Array.isArray(block)) {
                            for (const element of block) {
                                if (element.tag === 'text' && element.text) {
                                    textContent += element.text;
                                }
                                else if (element.tag === 'at' && element.user_name) {
                                    textContent += `@${element.user_name}`;
                                }
                            }
                            textContent += '\n';
                        }
                    }
                }
            }
        }
    }
    catch {
        textContent = event.content;
    }
    return textContent.trim();
}
/**
 * 处理调研群消息 - 收集所有消息（无需@）
 */
async function handleResearchMessage(event, token) {
    const chatId = event.chat_id;
    const senderId = event.sender.sender_id.open_id;
    const senderName = event.sender.sender_name || 'Unknown';
    const session = loadResearchSession(chatId);
    if (!session) {
        return { handled: false };
    }
    // 如果已完成或已取消，忽略
    if (session.status === 'completed' || session.status === 'cancelled') {
        return { handled: false, result: { reason: 'session_ended' } };
    }
    // 获取消息内容
    const textContent = extractTextFromEvent(event);
    // 检查是否是完成指令（任何人都可以触发）
    const completeKeywords = ['完成调研', '结束调研', '调研完成', '生成PRD', '完成'];
    const isCompleteCommand = completeKeywords.some(kw => textContent.includes(kw));
    // 检查是否是取消指令
    const cancelKeywords = ['取消', '不做了', '暂停', '停止'];
    const isCancelCommand = cancelKeywords.some(kw => textContent.includes(kw));
    // 检查是否超时
    const isExpired = isAutoCollectExpired(session);
    // 判断是否是需求人
    const isRequirementPerson = senderId === session.requirement_person_id;
    // 保存消息到记录（所有消息都保存）
    const chatMessage = {
        message_id: event.message_id,
        sender_id: senderId,
        sender_name: senderName,
        content: textContent,
        message_type: event.message_type,
        create_time: event.create_time,
        is_requirement_person: isRequirementPerson
    };
    addChatMessage(chatId, chatMessage);
    // 更新会话统计
    session.message_count = (session.message_count || 0) + 1;
    session.last_message_time = new Date().toISOString();
    saveResearchSession(session);
    console.log(`[调研群:${chatId.slice(-6)}] 收到消息 from ${senderName}: ${textContent.slice(0, 30)}... (总计: ${session.message_count}条)`);
    // 处理指令
    if (isCancelCommand) {
        // 只有需求人或Boss可以取消
        if (isRequirementPerson || senderId === session.boss_id) {
            session.status = 'cancelled';
            saveResearchSession(session);
            await (0, utils_1.sendFeishuMessage)(chatId, '❌ 需求调研已取消。如需重新开始，请重新触发需求跟进流程。', token);
            return { handled: true, result: { action: 'cancelled' } };
        }
    }
    if (isCompleteCommand || isExpired) {
        // 完成调研
        if (isCompleteCommand) {
            console.log(`收到完成指令，准备生成PRD`);
        }
        else if (isExpired) {
            console.log(`自动收集时间已到(${session.auto_collect_deadline})，准备生成PRD`);
            await (0, utils_1.sendFeishuMessage)(chatId, '⏰ 自动收集时间已到，正在生成PRD文档...', token);
        }
        session.status = 'completed';
        saveResearchSession(session);
        // 生成PRD（包含所有消息）
        await generatePRD(session, token);
        return { handled: true, result: { action: 'completed', triggered_by: isCompleteCommand ? 'command' : 'expired' } };
    }
    // 自动收集模式：保存消息即可，不需要回复
    if (session.auto_collect_mode) {
        // 可以在这里添加一些智能提示，但主要目标是收集所有消息
        if (session.message_count % 10 === 0) {
            await (0, utils_1.sendFeishuMessage)(chatId, `✅ 已收集 ${session.message_count} 条消息，继续收集需求信息...`, token);
        }
        return { handled: true, result: { action: 'collected', mode: 'auto' } };
    }
    // 问答模式：只处理需求人的回复
    if (!isRequirementPerson) {
        return { handled: true, result: { action: 'ignored', reason: 'not_requirement_person' } };
    }
    // 保存当前问题的回答
    const currentQuestion = exports.RESEARCH_QUESTIONS[session.current_question_idx];
    if (currentQuestion) {
        session.collected_data[currentQuestion.key] = textContent;
    }
    // 发送下一个问题
    session.current_question_idx++;
    if (session.current_question_idx < exports.RESEARCH_QUESTIONS.length) {
        const nextQuestion = exports.RESEARCH_QUESTIONS[session.current_question_idx];
        await (0, utils_1.sendFeishuMessage)(chatId, nextQuestion.question, token);
        saveResearchSession(session);
        return { handled: true, result: { action: 'next_question', idx: session.current_question_idx } };
    }
    else {
        // 所有问题回答完毕
        session.status = 'completed';
        saveResearchSession(session);
        // 生成PRD
        await generatePRD(session, token);
        return { handled: true, result: { action: 'completed' } };
    }
}
/**
 * 生成PRD文档
 */
async function generatePRD(session, token) {
    const chatId = session.chat_id;
    await (0, utils_1.sendFeishuMessage)(chatId, '📝 正在根据收集的信息生成PRD文档...', token);
    // 加载所有消息
    const messages = loadChatMessages(chatId);
    // 构建PRD内容
    let prdContent = `# ${session.requirement_title} - PRD文档\n\n`;
    prdContent += `**生成时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
    prdContent += `**需求人**: ${session.requirement_person_name}\n\n`;
    prdContent += `**消息总数**: ${messages.length}条\n\n`;
    prdContent += `---\n\n`;
    // 问答模式的数据
    if (!session.auto_collect_mode && Object.keys(session.collected_data).length > 0) {
        prdContent += `## 需求问答\n\n`;
        for (const question of exports.RESEARCH_QUESTIONS) {
            if (session.collected_data[question.key]) {
                prdContent += `### ${question.prd_section}\n\n`;
                prdContent += `**问题**: ${question.question}\n\n`;
                prdContent += `**回答**: ${session.collected_data[question.key]}\n\n`;
            }
        }
        prdContent += `---\n\n`;
    }
    // 所有聊天记录（自动收集模式）
    prdContent += `## 群聊记录\n\n`;
    for (const msg of messages) {
        const role = msg.is_requirement_person ? '【需求人】' : '';
        const time = new Date(msg.create_time).toLocaleString('zh-CN');
        prdContent += `**${msg.sender_name}**${role} (${time}):\n${msg.content}\n\n`;
    }
    // 保存PRD
    const prdDir = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'prd');
    if (!fs.existsSync(prdDir)) {
        fs.mkdirSync(prdDir, { recursive: true });
    }
    const prdFileName = `${session.requirement_title.slice(0, 30).replace(/[^\w\u4e00-\u9fa5]/g, '_')}_${Date.now()}.md`;
    const prdFilePath = path.join(prdDir, prdFileName);
    fs.writeFileSync(prdFilePath, prdContent, 'utf-8');
    // 发送完成通知
    const summaryMsg = `✅ **需求调研完成！**\n\n📄 **PRD文档已生成**\n• 消息总数: ${messages.length}条\n• 文件路径: ${prdFilePath}\n\n感谢大家的配合！本群将在3秒后自动解散。`;
    await (0, utils_1.sendFeishuMessage)(chatId, summaryMsg, token);
    console.log(`PRD已生成: ${prdFilePath}`);
}
/**
 * 获取调研统计信息
 */
function getResearchStats(chatId) {
    const session = loadResearchSession(chatId);
    if (!session) {
        return null;
    }
    return {
        messageCount: session.message_count || 0,
        status: session.status
    };
}
//# sourceMappingURL=research.js.map
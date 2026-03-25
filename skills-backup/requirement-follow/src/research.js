"use strict";
/**
 * 调研群消息处理模块
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
exports.ResearchHandler = exports.RESEARCH_QUESTIONS = void 0;
exports.formatQuestion = formatQuestion;
exports.loadResearchSession = loadResearchSession;
exports.saveResearchSession = saveResearchSession;
exports.deleteResearchSession = deleteResearchSession;
exports.loadChatMessages = loadChatMessages;
exports.saveChatMessages = saveChatMessages;
exports.addChatMessage = addChatMessage;
exports.isResearchChat = isResearchChat;
exports.isAutoCollectExpired = isAutoCollectExpired;
exports.createResearchSession = createResearchSession;
exports.startResearch = startResearch;
exports.handleResearchMessage = handleResearchMessage;
exports.getResearchStats = getResearchStats;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const RESEARCH_STATE_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research');
const RESEARCH_MESSAGES_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'research_messages');
const PRD_DIR = path.join(process.env.HOME || '', '.openclaw', 'feishu', 'prd');
[RESEARCH_STATE_DIR, RESEARCH_MESSAGES_DIR, PRD_DIR].forEach(dir => {
    if (!fs.existsSync(dir))
        fs.mkdirSync(dir, { recursive: true });
});
exports.RESEARCH_QUESTIONS = [
    {
        key: 'background',
        question: '👋 需求调研开始！\n\n📋 **需求**: {title}\n👤 **需求人**: @{requester}\n\n**问题 1/7：业务背景**\n请描述需求的业务背景和产生场景。',
        required: true,
        prd_section: '背景与目标'
    },
    {
        key: 'target_users',
        question: '**问题 2/7：目标用户**\n这个需求的目标用户是谁？',
        required: true,
        prd_section: '背景与目标'
    },
    {
        key: 'current_situation',
        question: '**问题 3/7：现状描述**\n请描述当前的系统/流程现状。',
        required: true,
        prd_section: '现状'
    },
    {
        key: 'pain_points',
        question: '**问题 4/7：核心痛点**\n当前的核心痛点是什么？',
        required: true,
        prd_section: '现状'
    },
    {
        key: 'expected_solution',
        question: '**问题 5/7：期望解决方案**\n您期望的解决方案是什么？',
        required: true,
        prd_section: '方案'
    },
    {
        key: 'priority',
        question: '**问题 6/7：优先级和时间**\n需求的优先级和时间要求是怎样的？',
        required: true,
        prd_section: '优先级和时间计划'
    },
    {
        key: 'attachments',
        question: '**问题 7/7：相关资料**\n是否有相关数据、截图、文档需要补充？',
        required: false,
        prd_section: '附件与参考资料'
    }
];
function formatQuestion(template, title, requester) {
    return template.replace(/\{title\}/g, title).replace(/\{requester\}/g, requester);
}
function getStateFilePath(chatId) {
    return path.join(RESEARCH_STATE_DIR, `${chatId}.json`);
}
function getMessagesFilePath(chatId) {
    return path.join(RESEARCH_MESSAGES_DIR, `${chatId}.json`);
}
function loadResearchSession(chatId) {
    try {
        const data = fs.readFileSync(getStateFilePath(chatId), 'utf-8');
        return JSON.parse(data);
    }
    catch {
        return null;
    }
}
function saveResearchSession(session) {
    session.updated_at = new Date().toISOString();
    fs.writeFileSync(getStateFilePath(session.chat_id), JSON.stringify(session, null, 2), 'utf-8');
}
function deleteResearchSession(chatId) {
    try {
        fs.unlinkSync(getStateFilePath(chatId));
    }
    catch { }
    try {
        fs.unlinkSync(getMessagesFilePath(chatId));
    }
    catch { }
}
function loadChatMessages(chatId) {
    try {
        return JSON.parse(fs.readFileSync(getMessagesFilePath(chatId), 'utf-8'));
    }
    catch {
        return [];
    }
}
function saveChatMessages(chatId, messages) {
    fs.writeFileSync(getMessagesFilePath(chatId), JSON.stringify(messages, null, 2), 'utf-8');
}
function addChatMessage(chatId, message) {
    const messages = loadChatMessages(chatId);
    if (!messages.some(m => m.message_id === message.message_id)) {
        messages.push(message);
        saveChatMessages(chatId, messages);
    }
}
function isResearchChat(chatId) {
    return loadResearchSession(chatId) !== null;
}
function isAutoCollectExpired(session) {
    return session.auto_collect_deadline ? new Date() > new Date(session.auto_collect_deadline) : false;
}
function extractTextFromEvent(event) {
    try {
        const content = JSON.parse(event.content);
        if (content.text)
            return content.text;
        if (content.post?.zh_cn) {
            let text = content.post.zh_cn.title || '';
            for (const block of content.post.zh_cn.content || []) {
                for (const item of block) {
                    if (item.tag === 'text')
                        text += item.text;
                    if (item.tag === 'at')
                        text += `@${item.user_name}`;
                }
            }
            return text;
        }
    }
    catch { }
    return event.content;
}
async function sendFeishuMessage(chatId, text, token) {
    try {
        const res = await fetch('https://open.feishu.cn/open-apis/im/v1/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ receive_id: chatId, msg_type: 'text', content: JSON.stringify({ text }) })
        });
        const data = await res.json();
        return data.code === 0;
    }
    catch {
        return false;
    }
}
function createResearchSession(chatId, title, personId, personName, bossId, recordId, mode = 'hybrid', hours = 24) {
    const now = new Date();
    const isAuto = mode === 'auto_collect' || mode === 'hybrid';
    const isQa = mode === 'qa' || mode === 'hybrid';
    const session = {
        chat_id: chatId, requirement_title: title, requirement_person_id: personId,
        requirement_person_name: personName, boss_id: bossId, record_id: recordId,
        current_question_idx: 0, collected_data: {}, attachments: [], status: 'waiting',
        created_at: now.toISOString(), updated_at: now.toISOString(), message_count: 0,
        mode, auto_collect_mode: isAuto, enable_qa: isQa, enable_auto_collect: isAuto,
        auto_collect_deadline: new Date(now.getTime() + hours * 3600000).toISOString(),
        processed_message_ids: []
    };
    saveResearchSession(session);
    return session;
}
async function startResearch(chatId, token) {
    const session = loadResearchSession(chatId);
    if (!session)
        return false;
    const deadline = session.auto_collect_deadline ? new Date(session.auto_collect_deadline).toLocaleString('zh-CN') : '24小时后';
    const welcome = session.auto_collect_mode
        ? `👋 需求调研群已创建！\n📋 **需求**: ${session.requirement_title}\n👤 **需求人**: ${session.requirement_person_name}\n\n我将自动收集本群消息用于生成PRD。\n⏰ 截止时间: ${deadline}\n\n发送「完成调研」结束收集，发送「取消」终止调研。`
        : `👋 需求调研开始！\n📋 **需求**: ${session.requirement_title}\n\n我将通过7个问题了解需求详情。`;
    await sendFeishuMessage(chatId, welcome, token);
    if (!session.auto_collect_mode) {
        await sendFeishuMessage(chatId, formatQuestion(exports.RESEARCH_QUESTIONS[0].question, session.requirement_title, session.requirement_person_name), token);
        session.current_question_idx = 0;
    }
    session.status = 'collecting';
    saveResearchSession(session);
    return true;
}
async function generatePRD(session, token) {
    await sendFeishuMessage(session.chat_id, '📝 正在生成PRD文档...', token);
    const messages = loadChatMessages(session.chat_id);
    let content = `# ${session.requirement_title} - PRD\n\n**需求人**: ${session.requirement_person_name}\n**消息数**: ${messages.length}条\n**模式**: ${session.mode}\n\n`;
    if (session.enable_qa && Object.keys(session.collected_data).length > 0) {
        content += '## 问答记录\n\n';
        for (const q of exports.RESEARCH_QUESTIONS) {
            if (session.collected_data[q.key]) {
                content += `**${q.prd_section}**: ${session.collected_data[q.key]}\n\n`;
            }
        }
    }
    content += '## 群聊记录\n\n';
    for (const m of messages) {
        content += `**${m.sender_name}**${m.is_requirement_person ? '【需求人】' : ''} (${new Date(m.create_time).toLocaleString('zh-CN')}): ${m.content}\n\n`;
    }
    const filename = `${session.requirement_title.slice(0, 30).replace(/[^\w\u4e00-\u9fa5]/g, '_')}_${Date.now()}.md`;
    const filepath = path.join(PRD_DIR, filename);
    fs.writeFileSync(filepath, content, 'utf-8');
    await sendFeishuMessage(session.chat_id, `✅ PRD已生成！\n📄 文件: ${filepath}\n\n本群将在3秒后解散。`, token);
}
async function handleResearchMessage(event, token) {
    const chatId = event.chat_id;
    const senderId = event.sender.sender_id.open_id;
    const senderName = event.sender.sender_name || 'Unknown';
    const session = loadResearchSession(chatId);
    if (!session)
        return { handled: false };
    if (session.status === 'completed' || session.status === 'cancelled')
        return { handled: false, result: { reason: 'session_ended' } };
    const text = extractTextFromEvent(event);
    const isReqPerson = senderId === session.requirement_person_id;
    const isBoss = senderId === session.boss_id;
    // 保存消息
    addChatMessage(chatId, { message_id: event.message_id, sender_id: senderId, sender_name: senderName, content: text, message_type: event.message_type, create_time: event.create_time, is_requirement_person: isReqPerson });
    session.message_count++;
    session.last_message_time = new Date().toISOString();
    saveResearchSession(session);
    // 指令处理
    const completeKeywords = ['完成调研', '结束调研', '调研完成', '生成PRD', '完成'];
    const cancelKeywords = ['取消', '不做了', '停止'];
    const isComplete = completeKeywords.some(k => text.includes(k));
    const isCancel = cancelKeywords.some(k => text.includes(k));
    const isExpired = isAutoCollectExpired(session);
    if (isCancel && (isReqPerson || isBoss)) {
        session.status = 'cancelled';
        saveResearchSession(session);
        await sendFeishuMessage(chatId, '❌ 需求调研已取消。', token);
        return { handled: true, result: { action: 'cancelled' } };
    }
    if (isComplete || isExpired) {
        if (isExpired)
            await sendFeishuMessage(chatId, '⏰ 自动收集时间到，正在生成PRD...', token);
        session.status = 'completed';
        saveResearchSession(session);
        await generatePRD(session, token);
        return { handled: true, result: { action: 'completed' } };
    }
    // 自动收集模式
    if (session.auto_collect_mode && !session.enable_qa) {
        if (session.message_count % 10 === 0) {
            await sendFeishuMessage(chatId, `✅ 已收集 ${session.message_count} 条消息`, token);
        }
        return { handled: true, result: { action: 'collected', mode: 'auto' } };
    }
    // 问答模式只处理需求人回复
    if (session.enable_qa && !isReqPerson) {
        return { handled: true, result: { action: 'ignored' } };
    }
    if (session.enable_qa) {
        const currentQ = exports.RESEARCH_QUESTIONS[session.current_question_idx];
        if (currentQ)
            session.collected_data[currentQ.key] = text;
        session.current_question_idx++;
        if (session.current_question_idx < exports.RESEARCH_QUESTIONS.length) {
            await sendFeishuMessage(chatId, formatQuestion(exports.RESEARCH_QUESTIONS[session.current_question_idx].question, session.requirement_title, session.requirement_person_name), token);
            saveResearchSession(session);
            return { handled: true, result: { action: 'next_question' } };
        }
        else {
            session.status = 'completed';
            saveResearchSession(session);
            await generatePRD(session, token);
            return { handled: true, result: { action: 'completed' } };
        }
    }
    return { handled: true, result: { action: 'collected' } };
}
function getResearchStats(chatId) {
    const session = loadResearchSession(chatId);
    return session ? { messageCount: session.message_count || 0, status: session.status } : null;
}
class ResearchHandler {
    constructor(token) { this.token = token; }
    async handleMessage(event) { return handleResearchMessage(event, this.token); }
    isResearchChat(chatId) { return isResearchChat(chatId); }
    getStats(chatId) { return getResearchStats(chatId); }
}
exports.ResearchHandler = ResearchHandler;
exports.default = ResearchHandler;
//# sourceMappingURL=research.js.map
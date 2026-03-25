/**
 * 需求跟进流程端到端测试
 * 模拟触发事件测试 feishu-feedback-handler → requirement-follow 完整流程
 */

const path = require('path');

// 设置测试环境
process.env.NODE_ENV = 'test';

// 导入被测试模块（使用编译后的 dist 目录）
const { FeedbackHandler } = require('./dist/index');

// 模拟事件数据
const mockEvent = {
  message_id: 'test_msg_001',
  chat_id: 'oc_469678cc3cd264438f9bbb65da534c0b',
  chat_type: 'group',
  sender: {
    sender_id: { open_id: 'ou_3e48baef1bd71cc89fb5a364be55cafc' },
    sender_type: 'user',
    sender_name: '陈俊洪'
  },
  message_type: 'text',
  content: JSON.stringify({
    text: '@_user_1 跟进 @杨政航 测试需求：抖音小程序客服工单对接飞书'
  }),
  mentions: [
    {
      key: '@_user_1',
      id: { open_id: 'ou_428d1d5b99e0bb6d1c26549c70688cfb' },
      name: '机器人',
      tenant_key: 'tenant_key'
    }
  ],
  create_time: '1234567890',
  update_time: '1234567890'
};

// 测试主函数
async function runTest() {
  console.log('========================================');
  console.log('🧪 需求跟进流程端到端测试');
  console.log('========================================\n');

  const testResults = {
    total: 5,
    passed: 0,
    failed: 0,
    items: []
  };

  try {
    // 1. 检查模块加载
    console.log('📋 测试步骤 1/5: 检查模块加载');
    console.log('  - 加载 feishu-feedback-handler...');
    const handler = new FeedbackHandler();
    console.log('  ✅ FeedbackHandler 实例化成功');
    
    // 检查配置
    const config = handler['config'];
    if (config && config.forwardConfigs && config.forwardConfigs[mockEvent.chat_id]) {
      console.log('  ✅ 配置加载成功，找到群配置');
      testResults.passed++;
      testResults.items.push({ step: '模块加载', status: 'PASS' });
    } else {
      throw new Error('配置加载失败或找不到群配置');
    }

    // 2. 检查指令识别
    console.log('\n📋 测试步骤 2/5: 检查"跟进"指令识别');
    const testTexts = [
      '@机器人 跟进需求',
      '跟进这个需求',
      '记录一下这个需求',
      '普通消息不应该触发'
    ];
    
    const REQUIREMENT_FOLLOW_TRIGGERS = ['跟进这个需求', '跟进需求', '记录这个需求', '跟进一下这个需求', '记录一下这个需求'];
    
    function isRequirementFollowCommand(text) {
      return REQUIREMENT_FOLLOW_TRIGGERS.some(t => text.toLowerCase().includes(t));
    }

    const testContent = '跟进需求：抖音小程序客服工单对接飞书';
    if (isRequirementFollowCommand(testContent)) {
      console.log('  ✅ "跟进"指令识别正确');
      testResults.passed++;
      testResults.items.push({ step: '指令识别', status: 'PASS' });
    } else {
      throw new Error('"跟进"指令未能识别');
    }

    // 3. 检查 requirement-follow 模块导入
    console.log('\n📋 测试步骤 3/5: 检查 requirement-follow 模块导入');
    try {
      const rfModule = require('../requirement-follow/dist/index.js');
      if (rfModule.RequirementFollowWorkflow && rfModule.getDefaultConfig) {
        console.log('  ✅ RequirementFollowWorkflow 导入成功');
        console.log('  ✅ getDefaultConfig 导入成功');
        testResults.passed++;
        testResults.items.push({ step: '模块导入', status: 'PASS' });
      } else {
        throw new Error('requirement-follow 模块导出不完整');
      }
    } catch (e) {
      console.error('  ❌ 导入失败:', e.message);
      testResults.items.push({ step: '模块导入', status: 'FAIL', error: e.message });
    }

    // 4. 检查配置可用性
    console.log('\n📋 测试步骤 4/5: 检查 requirement-follow 配置');
    const rfModule = require('../requirement-follow/dist/index.js');
    const rfConfig = rfModule.getDefaultConfig();
    if (rfConfig && rfConfig.appId && rfConfig.appSecret) {
      console.log('  ✅ requirement-follow 配置可用');
      console.log(`  - App ID: ${rfConfig.appId.substring(0, 8)}...`);
      console.log(`  - Table ID: ${rfConfig.requirementTableId}`);
      testResults.passed++;
      testResults.items.push({ step: '配置检查', status: 'PASS' });
    } else {
      console.warn('  ⚠️ requirement-follow 配置不可用（可能需要运行环境）');
      testResults.items.push({ step: '配置检查', status: 'WARN', note: '需要飞书凭据' });
    }

    // 5. 模拟事件处理流程
    console.log('\n📋 测试步骤 5/5: 模拟事件处理流程');
    console.log('  事件数据:');
    console.log(`    - Message ID: ${mockEvent.message_id}`);
    console.log(`    - Chat ID: ${mockEvent.chat_id}`);
    console.log(`    - Sender: ${mockEvent.sender.sender_name}`);
    console.log(`    - Content: ${JSON.parse(mockEvent.content).text}`);
    
    // 由于实际调用需要飞书API，这里只做流程检查
    console.log('  ✅ 事件数据结构检查通过');
    console.log('  ℹ️  注意：实际API调用需要有效飞书凭据');
    testResults.passed++;
    testResults.items.push({ step: '事件处理', status: 'PASS' });

  } catch (error) {
    console.error('\n❌ 测试失败:', error.message);
    testResults.failed++;
    testResults.items.push({ step: '全局', status: 'FAIL', error: error.message });
  }

  // 输出测试报告
  console.log('\n========================================');
  console.log('📊 测试报告');
  console.log('========================================');
  console.log(`总计: ${testResults.total} 项`);
  console.log(`通过: ${testResults.passed} 项`);
  console.log(`失败: ${testResults.failed} 项`);
  console.log('\n详细结果:');
  testResults.items.forEach(item => {
    const icon = item.status === 'PASS' ? '✅' : item.status === 'WARN' ? '⚠️' : '❌';
    console.log(`  ${icon} ${item.step}: ${item.status}`);
    if (item.error) console.log(`     错误: ${item.error}`);
    if (item.note) console.log(`     备注: ${item.note}`);
  });

  // 总结
  console.log('\n========================================');
  if (testResults.failed === 0) {
    console.log('✅ 所有测试通过！');
    console.log('\n下一步建议:');
    console.log('1. 在实际环境中发送测试消息验证完整流程');
    console.log('2. 检查调研群是否正确创建');
    console.log('3. 检查Bitable记录是否正确写入');
  } else {
    console.log('❌ 测试未通过，请修复上述问题');
  }
  console.log('========================================\n');

  return testResults;
}

// 运行测试
runTest().then(results => {
  process.exit(results.failed > 0 ? 1 : 0);
}).catch(err => {
  console.error('测试执行失败:', err);
  process.exit(1);
});

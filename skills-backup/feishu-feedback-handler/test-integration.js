/**
 * 需求跟进流程完整集成测试
 * 实际调用飞书API测试完整流程
 */

const { FeedbackHandler } = require('./dist/index');

// 模拟事件数据 - 使用真实用户ID
const mockEvent = {
  message_id: 'test_msg_' + Date.now(),
  chat_id: 'oc_469678cc3cd264438f9bbb65da534c0b',
  chat_type: 'group',
  sender: {
    sender_id: { open_id: 'ou_3e48baef1bd71cc89fb5a364be55cafc' },
    sender_type: 'user',
    sender_name: '陈俊洪'
  },
  message_type: 'text',
  content: JSON.stringify({
    text: '@_user_1 跟进需求：抖音小程序客服工单对接飞书集成测试'
  }),
  mentions: [
    {
      key: '@_user_1',
      id: { open_id: 'ou_428d1d5b99e0bb6d1c26549c70688cfb' },
      name: '机器人',
      tenant_key: 'tenant_key'
    }
  ],
  create_time: String(Math.floor(Date.now() / 1000)),
  update_time: String(Math.floor(Date.now() / 1000))
};

// 测试主函数
async function runIntegrationTest() {
  console.log('========================================');
  console.log('🔬 需求跟进流程集成测试');
  console.log('========================================\n');
  
  console.log('测试配置:');
  console.log(`  - 目标群: ${mockEvent.chat_id}`);
  console.log(`  - 发送者: ${mockEvent.sender.sender_name}`);
  console.log(`  - 消息内容: ${JSON.parse(mockEvent.content).text}`);
  console.log('');

  const results = {
    steps: [],
    errors: [],
    data: {}
  };

  try {
    // 1. 初始化 Handler
    console.log('📌 Step 1: 初始化 FeedbackHandler');
    const handler = new FeedbackHandler();
    console.log('  ✅ FeedbackHandler 初始化成功\n');
    results.steps.push({ step: 1, name: '初始化 Handler', status: 'PASS' });

    // 2. 处理消息
    console.log('📌 Step 2: 处理模拟消息事件');
    console.log('  调用 handler.handleMessage()...');
    
    const result = await handler.handleMessage(mockEvent);
    
    console.log('  ✅ 消息处理完成');
    console.log('  返回结果:');
    console.log(JSON.stringify(result, null, 2));
    
    results.steps.push({ step: 2, name: '消息处理', status: 'PASS', result });
    results.data = result;

    // 3. 验证结果
    console.log('\n📌 Step 3: 验证处理结果');
    
    const checks = [
      { name: '已处理标记', pass: result.handled === true },
      { name: '类型标识', pass: result.type === 'requirement_follow' },
      { name: '成功状态', pass: result.success === true },
      { name: '记录ID存在', pass: !!result.recordId },
      { name: '群ID存在', pass: !!result.chatId },
      { name: '群名称存在', pass: !!result.chatName }
    ];
    
    checks.forEach(check => {
      const icon = check.pass ? '✅' : '❌';
      console.log(`  ${icon} ${check.name}`);
    });
    
    const allPassed = checks.every(c => c.pass);
    results.steps.push({ 
      step: 3, 
      name: '结果验证', 
      status: allPassed ? 'PASS' : 'FAIL',
      checks 
    });

    if (allPassed) {
      console.log('\n✅ 所有验证通过！');
    } else {
      console.log('\n❌ 部分验证失败');
    }

  } catch (error) {
    console.error('\n❌ 测试执行失败:');
    console.error(`  错误: ${error.message}`);
    console.error(`  堆栈: ${error.stack}`);
    results.errors.push({ message: error.message, stack: error.stack });
    results.steps.push({ step: 'ERROR', name: '执行异常', status: 'FAIL', error: error.message });
  }

  // 输出总结
  console.log('\n========================================');
  console.log('📊 集成测试总结');
  console.log('========================================');
  
  const passed = results.steps.filter(s => s.status === 'PASS').length;
  const failed = results.steps.filter(s => s.status === 'FAIL').length;
  
  console.log(`执行步骤: ${results.steps.length}`);
  console.log(`通过: ${passed}`);
  console.log(`失败: ${failed}`);
  
  if (results.data && results.data.recordId) {
    console.log(`\n创建的记录ID: ${results.data.recordId}`);
  }
  if (results.data && results.data.chatId) {
    console.log(`创建的调研群ID: ${results.data.chatId}`);
  }
  if (results.data && results.data.chatName) {
    console.log(`调研群名称: ${results.data.chatName}`);
  }
  
  if (results.errors.length > 0) {
    console.log('\n错误详情:');
    results.errors.forEach((err, idx) => {
      console.log(`  ${idx + 1}. ${err.message}`);
    });
  }
  
  console.log('\n========================================');
  
  return results;
}

// 运行测试
runIntegrationTest().then(results => {
  const hasFailed = results.steps.some(s => s.status === 'FAIL') || results.errors.length > 0;
  process.exit(hasFailed ? 1 : 0);
}).catch(err => {
  console.error('测试异常:', err);
  process.exit(1);
});

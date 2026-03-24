# 问题跟进数据校验规范 - 经验教训

**日期**: 2026-03-23  
**问题**: Bitable反馈表第20/21条记录时间戳错误  
**影响**: 超时提醒脚本误报"超期365天"，错误发送群消息

---

## 问题经过

1. **录入时间错误**：第20/21条记录的时间戳为 `1742691720000`（2025-03-23），但实际应为今天（2026-03-23）
2. **脚本误报**：`check_overdue_issues.py` 计算出超期365天，触发3天超时群提醒
3. **干扰群消息**：错误地向猛龙队开发群发送了"严重超时提醒"

---

## 根本原因

### 1. 数据录入时缺乏校验
- 复制旧记录模板时，未更新「反馈时间」字段
- 未校验时间戳是否合理（2025年的时间出现在2026年的记录中）

### 2. 写入后未验证
- 创建记录后没有读取验证关键字段
- 如果验证就会发现时间异常

### 3. 脚本缺乏防御性检查
- 脚本直接信任数据源，没有对超过30天的"新记录"进行警告

---

## 解决方案

### 立即修复
- ✅ 修改第20条记录的时间为今天（2026-03-23）
- ✅ 删除第21条重复记录

### 长期预防（已更新到 skill）

**数据写入前校验：**
```python
def validate_feedback_timestamp(timestamp_ms: int) -> tuple[bool, str]:
    now = datetime.now()
    feedback_time = datetime.fromtimestamp(timestamp_ms / 1000)
    
    # 不能是未来时间
    if feedback_time > now + timedelta(minutes=5):
        return False, "反馈时间不能是未来"
    
    # 不能超过30天（防止复制旧记录）
    if feedback_time < now - timedelta(days=30):
        return False, "反馈时间超过30天前，可能是复制了旧记录"
    
    return True, "通过"
```

**数据写入后验证：**
- 创建记录后立即读取验证
- 检查关键字段（反馈时间、处理状态等）

---

## 责任归属

- **我的错误**：
  1. 复制旧记录时未更新时间戳
  2. 写入后未验证数据
  3. 执行测试脚本时未使用 dry-run 模式，直接发送了群消息

- **改进措施**：
  1. 每次写入Bitable前执行时间戳校验
  2. 写入后必须读取验证
  3. 测试有副作用的脚本时，先询问Boss是否使用 `--dry-run`

---

## 相关文件更新

- `/home/admin/openclaw/workspace/skills/feishu_forward/SKILL.md` - 添加了「数据录入规范」章节
- `/home/admin/openclaw/workspace/check_overdue_issues.py` - 已添加「处理中」状态的群提醒

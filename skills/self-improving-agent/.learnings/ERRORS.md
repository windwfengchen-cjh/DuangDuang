# Errors Log

Command failures, exceptions, and unexpected behaviors.

---

## [ERR-20260319-001] lock_json_parse

**Logged**: 2026-03-19T20:21:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
self_improve.py 在解析 lock.json 时遇到数据结构异常

### Error
```
AttributeError: 'list' object has no attribute 'get'
File "self_improve.py", line 111, in check_skills_version
```

### Context
- 时间: 2026-03-19 19:23:43
- 操作: 自动执行 self_improve.py 检查技能版本
- 影响: 技能版本检查流程中断

### Suggested Fix
1. 在 check_skills_version() 中添加类型检查
2. 确保 info 是字典类型再调用 .get()
3. 添加异常处理，记录异常数据结构

### Metadata
- Reproducible: yes
- Related Files: self_improve.py, .clawhub/lock.json
- Tags: lock.json, parsing, type-error

---

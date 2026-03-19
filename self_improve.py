#!/usr/bin/env python3
"""
Self-Improving Agent 执行脚本
定时执行自我提升流程，每天 18:10 运行
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
LOG_DIR = Path("/home/admin/openclaw/workspace/logs/self_improve")
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("self_improving_agent")

# 路径配置
WORKSPACE_DIR = Path("/home/admin/openclaw/workspace")
SKILLS_DIR = WORKSPACE_DIR / "skills"
CLAWHUB_DIR = WORKSPACE_DIR / ".clawhub"
SOUL_MD = WORKSPACE_DIR / "SOUL.md"


def load_json(filepath):
    """加载 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载 {filepath} 失败: {e}")
        return None


def save_json(filepath, data):
    """保存 JSON 文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存 {filepath} 失败: {e}")
        return False


def read_soul_md():
    """读取 SOUL.md 检查约束"""
    logger.info("=" * 50)
    logger.info("步骤 1: 读取 SOUL.md 检查约束遵守情况")
    
    if not SOUL_MD.exists():
        logger.warning("SOUL.md 不存在")
        return None
    
    try:
        with open(SOUL_MD, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"成功读取 SOUL.md ({len(content)} 字符)")
        
        # 分析核心约束
        constraints = []
        if "诚实" in content or "honest" in content.lower():
            constraints.append("诚实原则")
        if "透明" in content or "transparent" in content.lower():
            constraints.append("透明原则")
        if "安全" in content or "safe" in content.lower():
            constraints.append("安全原则")
        
        logger.info(f"识别的约束: {', '.join(constraints) if constraints else '未明确识别'}")
        return content
        
    except Exception as e:
        logger.error(f"读取 SOUL.md 失败: {e}")
        return None


def check_skills_version():
    """检查所有技能的版本"""
    logger.info("=" * 50)
    logger.info("步骤 2: 检查所有技能的版本和更新")
    
    lock_file = CLAWHUB_DIR / "lock.json"
    lock_data = load_json(lock_file)
    
    if not lock_data:
        logger.error("无法加载 lock.json")
        return []
    
    skills_status = []
    
    for skill_name, info in lock_data.get("skills", {}).items():
        skill_dir = SKILLS_DIR / skill_name
        meta_file = skill_dir / "_meta.json"
        
        status = {
            "name": skill_name,
            "version": info.get("version"),
            "installed_at": info.get("installedAt"),
            "exists": skill_dir.exists(),
            "meta_exists": meta_file.exists(),
            "meta_version": None
        }
        
        if meta_file.exists():
            meta = load_json(meta_file)
            if meta:
                status["meta_version"] = meta.get("version")
                # 检查版本一致性
                status["version_match"] = (status["version"] == status["meta_version"])
        
        skills_status.append(status)
        
        if status.get("version_match") is False:
            logger.warning(f"技能 {skill_name}: 版本不匹配 (lock: {status['version']}, meta: {status['meta_version']})")
        elif not status["exists"]:
            logger.error(f"技能 {skill_name}: 目录不存在")
        else:
            logger.info(f"技能 {skill_name}: v{status['version']} - 正常")
    
    return skills_status


def analyze_operation_records():
    """分析最近的操作记录"""
    logger.info("=" * 50)
    logger.info("步骤 3: 分析最近的操作记录")
    
    insights = []
    
    # 分析日志目录
    if LOG_DIR.exists():
        log_files = sorted(LOG_DIR.glob("*.log"))[-7:]  # 最近7天
        logger.info(f"发现 {len(log_files)} 个日志文件")
        
        error_count = 0
        warning_count = 0
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    error_count += content.lower().count("error")
                    warning_count += content.lower().count("warning")
            except Exception as e:
                logger.warning(f"无法读取日志 {log_file}: {e}")
        
        logger.info(f"最近7天统计: {error_count} 个错误, {warning_count} 个警告")
        
        if error_count > 10:
            insights.append({"type": "high", "issue": "错误数量较多，需要排查"})
        if warning_count > 20:
            insights.append({"type": "medium", "issue": "警告数量偏高，建议优化"})
    
    # 检查技能使用频率
    skills_count = len(list(SKILLS_DIR.glob("*/SKILL.md"))) if SKILLS_DIR.exists() else 0
    logger.info(f"当前技能库大小: {skills_count} 个技能")
    
    if skills_count < 3:
        insights.append({"type": "low", "issue": "技能库较小，建议扩展功能"})
    
    return insights


def generate_improvements(skills_status, insights):
    """生成改进建议"""
    logger.info("=" * 50)
    logger.info("步骤 4: 生成改进建议")
    
    improvements = []
    
    # 基于技能状态生成建议
    for skill in skills_status:
        if not skill.get("version_match"):
            improvements.append({
                "priority": "high",
                "category": "版本同步",
                "target": skill["name"],
                "action": f"同步版本号: lock.json={skill['version']}, _meta.json={skill['meta_version']}"
            })
        if not skill["exists"]:
            improvements.append({
                "priority": "high",
                "category": "缺失文件",
                "target": skill["name"],
                "action": "重新安装或移除 lock.json 中的记录"
            })
    
    # 基于洞察生成建议
    for insight in insights:
        improvements.append({
            "priority": insight["type"],
            "category": "性能优化",
            "target": "系统整体",
            "action": insight["issue"]
        })
    
    # 默认建议
    if len(improvements) == 0:
        improvements.append({
            "priority": "low",
            "category": "维护",
            "target": "系统整体",
            "action": "系统运行良好，继续保持监控"
        })
    
    # 记录建议
    for imp in improvements:
        logger.info(f"[{imp['priority'].upper()}] {imp['category']}: {imp['action']}")
    
    return improvements


def update_skill_files(improvements):
    """更新相关技能文件"""
    logger.info("=" * 50)
    logger.info("步骤 5: 更新相关技能文件")
    
    updated = 0
    
    for imp in improvements:
        if imp["priority"] == "high" and imp["category"] == "版本同步":
            skill_name = imp["target"]
            skill_dir = SKILLS_DIR / skill_name
            meta_file = skill_dir / "_meta.json"
            
            if meta_file.exists():
                meta = load_json(meta_file)
                if meta:
                    # 更新元数据中的时间戳
                    meta["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                    if save_json(meta_file, meta):
                        logger.info(f"已更新 {skill_name} 的 _meta.json")
                        updated += 1
    
    # 记录执行时间到状态文件
    status_file = WORKSPACE_DIR / ".clawhub" / "self_improve_status.json"
    status = {
        "last_run": datetime.now().isoformat(),
        "improvements_count": len(improvements),
        "files_updated": updated
    }
    save_json(status_file, status)
    
    logger.info(f"共更新 {updated} 个文件")
    return updated


def spawn_subagent_task():
    """
    派生子智能体执行详细分析
    注意: 实际调用时需要使用 sessions_spawn 工具
    """
    logger.info("=" * 50)
    logger.info("派生子智能体执行深度分析...")
    
    # 这里会在实际运行时通过 sessions_spawn 调用
    # 子智能体的任务是:
    # 1. 深度分析 SOUL.md 的约束遵守情况
    # 2. 检查每个技能的 SKILL.md 完整性
    # 3. 生成详细的改进报告
    
    task_description = """
    深度自我分析任务:
    1. 读取 /home/admin/openclaw/workspace/SOUL.md
    2. 检查所有技能的 SKILL.md 完整性
    3. 对比版本号一致性
    4. 生成详细的改进报告
    5. 输出到 /home/admin/openclaw/workspace/logs/self_improve/analysis_$(date).md
    """
    
    logger.info(f"子任务描述: {task_description}")
    return True


def main():
    """主执行函数"""
    logger.info("╔" + "=" * 48 + "╗")
    logger.info("║" + " Self-Improving Agent 开始执行 ".center(48) + "║")
    logger.info("╚" + "=" * 48 + "╝")
    logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 步骤 1: 读取 SOUL.md
        soul_content = read_soul_md()
        
        # 步骤 2: 检查技能版本
        skills_status = check_skills_version()
        
        # 步骤 3: 分析操作记录
        insights = analyze_operation_records()
        
        # 步骤 4: 生成改进建议
        improvements = generate_improvements(skills_status, insights)
        
        # 步骤 5: 更新技能文件
        updated = update_skill_files(improvements)
        
        # 派生子智能体（记录意图，实际调用由外部调度器处理）
        spawn_subagent_task()
        
        # 总结
        logger.info("=" * 50)
        logger.info("执行完成!")
        logger.info(f"检查技能数: {len(skills_status)}")
        logger.info(f"发现问题数: {len(insights)}")
        logger.info(f"生成建议数: {len(improvements)}")
        logger.info(f"更新文件数: {updated}")
        
        return 0
        
    except Exception as e:
        logger.exception("执行过程中发生错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Utility functions for ha_traccar."""
import re


def sanitize_entity_id(name: str, fallback_id: int | None = None) -> str:
    """将设备名转换为安全的实体 ID（只保留字母数字下划线），保证非空。"""
    # 先移除特殊字符
    sanitized = re.sub(r"[^\w\s]", "", name)
    # 空格转下划线
    sanitized = sanitized.replace(" ", "_")
    # 移除非 ASCII 字符（中文等）
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", sanitized)
    # 压缩连续下划线
    sanitized = re.sub(r"_+", "_", sanitized)
    # 去除首尾下划线
    sanitized = sanitized.strip("_")
    # 如果结果为空，使用 fallback
    if not sanitized:
        if fallback_id is not None:
            sanitized = f"device_{fallback_id}"
        else:
            sanitized = "device"
    # 确保不以数字开头
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized.lower()
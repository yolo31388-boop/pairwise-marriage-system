"""结婚系统入口(兼容旧导入路径, 实现在 marriage/system.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from marriage.system import (  # noqa: E402,F401
    FORCED_DIVORCE_OTHER_RATIO,
    FORCED_DIVORCE_PROPOSER_RATIO,
    Marriage,
    MarriageSystem,
    PROPOSE_MIN_LEVEL,
    SKILL_BASE_CHANCE,
    SKILL_INTIMACY_CAP,
    SKILL_MAX_CHANCE,
    SKILL_YEARS_CAP,
    TELEPORT_BANNED_SCENES,
    TELEPORT_COOLDOWN,
    WAREHOUSE_CAPACITY,
    WEDDING_REWARDS,
    WEDDING_TIER_ALIASES,
    YEAR_SECONDS,
)

__all__ = [
    "Marriage",
    "MarriageSystem",
    "PROPOSE_MIN_LEVEL",
    "SKILL_BASE_CHANCE",
    "SKILL_MAX_CHANCE",
    "TELEPORT_COOLDOWN",
    "TELEPORT_BANNED_SCENES",
    "WAREHOUSE_CAPACITY",
    "WEDDING_REWARDS",
    "YEAR_SECONDS",
]

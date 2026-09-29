"""结婚系统 - 带7个bug"""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Marriage:
    husband: str
    wife: str
    marry_time: float
    intimacy: int

class MarriageSystem:
    def __init__(self):
        self.marriages: list[Marriage] = []
        self.shared_inventory = {}  # bug5: 未实现

    def propose(self, p1, p2, level):
        # bug1: 不检查单身
        if level >= 30:
            return True
        return False

    def get_wedding_reward(self, tier):
        # bug2: 固定奖励
        return {"gold": 1000}

    def get_couple_skill_chance(self, marriage):
        # bug3: 固定概率
        return 0.2

    def divorce(self, proposer, marriage):
        # bug4: 提出方净身出户
        return {"proposer_get": 0, "other_get": "all"}

    def get_anniversary_reward(self, marriage, year):
        # bug6: 无记录
        return {"gift": "rose"}

    def couple_teleport(self, p1, p2, scene):
        # bug7: 无冷却无限制
        return True

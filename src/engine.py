"""结婚系统 - 7个bug已修复"""
import time
from dataclasses import dataclass, field

PROPOSE_MIN_LEVEL = 30
SKILL_BASE_CHANCE = 0.2
SKILL_MAX_CHANCE = 0.8
TELEPORT_COOLDOWN = 30 * 60  # 30分钟
TELEPORT_BANNED_SCENES = {"dungeon", "battlefield"}
WAREHOUSE_CAPACITY = 100

WEDDING_REWARDS = {
    "normal": {"gold": 1000, "items": ["喜糖"]},
    "luxury": {"gold": 10000, "title": "神仙眷侣", "items": ["豪华婚戒", "双人坐骑"]},
}


@dataclass
class Marriage:
    husband: str
    wife: str
    marry_time: float
    intimacy: int
    pre_marriage_assets: dict = field(default_factory=dict)   # 婚前财产 {player: assets}
    post_marriage_assets: dict = field(default_factory=dict)  # 婚后共同财产
    claimed_anniversaries: set = field(default_factory=set)   # 已领取的纪念日年份
    last_teleport_time: float = 0.0

    def years_married(self, now=None):
        now = time.time() if now is None else now
        return max(0, int((now - self.marry_time) // (365 * 24 * 3600)))


class MarriageSystem:
    def __init__(self):
        self.marriages: list[Marriage] = []
        self.shared_inventory = {}  # 夫妻仓库 {couple_key: {item: count}}

    # ---- 工具 ----
    def _find_marriage(self, player):
        for m in self.marriages:
            if player in (m.husband, m.wife):
                return m
        return None

    def _couple_key(self, marriage):
        return tuple(sorted((marriage.husband, marriage.wife)))

    def _is_single(self, player):
        return self._find_marriage(player) is None

    # ---- bug1: 求婚需双方单身且等级达标 ----
    def propose(self, p1, p2, level):
        if level < PROPOSE_MIN_LEVEL:
            return False
        if p1 == p2:
            return False
        if not (self._is_single(p1) and self._is_single(p2)):
            return False
        return True

    # ---- bug2: 婚礼奖励按档次区分 ----
    def get_wedding_reward(self, tier):
        return dict(WEDDING_REWARDS.get(tier, WEDDING_REWARDS["normal"]))

    # ---- bug3: 技能概率随亲密度和婚龄提升 ----
    def get_couple_skill_chance(self, marriage, now=None):
        intimacy_bonus = min(marriage.intimacy, 1000) / 1000 * 0.3
        years_bonus = min(marriage.years_married(now), 10) * 0.03
        return min(SKILL_MAX_CHANCE, SKILL_BASE_CHANCE + intimacy_bonus + years_bonus)

    # ---- bug4: 离婚财产分割（协议/强制） ----
    def divorce(self, proposer, marriage, forced=False):
        other = marriage.wife if proposer == marriage.husband else marriage.husband
        pre = marriage.pre_marriage_assets
        post = dict(marriage.post_marriage_assets)
        result = {
            proposer: {"pre": pre.get(proposer, {}), "post": {}},
            other: {"pre": pre.get(other, {}), "post": {}},
        }
        if forced:
            # 强制离婚：提出方只能分30%婚后财产
            ratio_proposer, ratio_other = 0.3, 0.7
        else:
            # 协议离婚：婚后财产平分
            ratio_proposer = ratio_other = 0.5
        for asset, value in post.items():
            result[proposer]["post"][asset] = value * ratio_proposer
            result[other]["post"][asset] = value * ratio_other
        if marriage in self.marriages:
            self.marriages.remove(marriage)
        self.shared_inventory.pop(self._couple_key(marriage), None)
        return result

    # ---- bug5: 夫妻仓库（有额度限制） ----
    def _warehouse(self, marriage):
        return self.shared_inventory.setdefault(self._couple_key(marriage), {})

    def deposit(self, player, marriage, item, count=1):
        if player not in (marriage.husband, marriage.wife) or count <= 0:
            return False
        wh = self._warehouse(marriage)
        if sum(wh.values()) + count > WAREHOUSE_CAPACITY:
            return False
        wh[item] = wh.get(item, 0) + count
        return True

    def withdraw(self, player, marriage, item, count=1):
        if player not in (marriage.husband, marriage.wife) or count <= 0:
            return False
        wh = self._warehouse(marriage)
        if wh.get(item, 0) < count:
            return False
        wh[item] -= count
        if wh[item] == 0:
            del wh[item]
        return True

    # ---- bug6: 纪念日奖励按婚龄递增且有领取记录 ----
    def get_anniversary_reward(self, marriage, year):
        if year < 1 or year > marriage.years_married():
            return None
        if year in marriage.claimed_anniversaries:
            return None
        marriage.claimed_anniversaries.add(year)
        return {"gift": "rose", "gold": 1000 * year, "title": f"结婚{year}周年"}

    # ---- bug7: 夫妻传送有冷却且限制场景 ----
    def couple_teleport(self, p1, p2, scene, now=None):
        if scene in TELEPORT_BANNED_SCENES:
            return False
        marriage = self._find_marriage(p1)
        if marriage is None or p2 not in (marriage.husband, marriage.wife):
            return False
        now = time.time() if now is None else now
        if now - marriage.last_teleport_time < TELEPORT_COOLDOWN:
            return False
        marriage.last_teleport_time = now
        return True

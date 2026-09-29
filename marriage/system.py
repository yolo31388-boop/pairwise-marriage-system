"""结婚系统 - 7个bug已修复

修复点:
1. 求婚同时检查双方等级与婚姻状态, 已婚不能再求婚
2. 婚礼奖励按档次区分, 豪华婚礼有专属称号和道具
3. 夫妻技能触发概率随亲密度和婚龄提升
4. 离婚财产区分婚前/婚后, 支持协议离婚与强制离婚
5. 夫妻仓库, 双方可存取, 有额度限制
6. 纪念日奖励按婚龄递增, 且有领取记录防重复
7. 夫妻传送有冷却(30分钟), 副本/战场不可用
"""
import time
from dataclasses import dataclass, field

PROPOSE_MIN_LEVEL = 30
SKILL_BASE_CHANCE = 0.2
SKILL_MAX_CHANCE = 0.8
SKILL_INTIMACY_CAP = 1000
SKILL_YEARS_CAP = 10
TELEPORT_COOLDOWN = 30 * 60
TELEPORT_BANNED_SCENES = {"dungeon", "battlefield", "副本", "战场", "战场场景"}
WAREHOUSE_CAPACITY = 100
YEAR_SECONDS = 365 * 24 * 3600

WEDDING_REWARDS = {
    "normal": {
        "gold": 1000,
        "title": "新婚燕尔",
        "items": ["喜糖"],
    },
    "luxury": {
        "gold": 10000,
        "title": "神仙眷侣",
        "items": ["豪华婚戒", "双人坐骑", "喜糖"],
    },
}
WEDDING_TIER_ALIASES = {
    "普通": "normal",
    "普通婚礼": "normal",
    "豪华": "luxury",
    "豪华婚礼": "luxury",
}

FORCED_DIVORCE_PROPOSER_RATIO = 0.3
FORCED_DIVORCE_OTHER_RATIO = 0.7


@dataclass
class Marriage:
    husband: str
    wife: str
    marry_time: float
    intimacy: int = 0
    pre_marriage_assets: dict = field(default_factory=dict)
    post_marriage_assets: dict = field(default_factory=dict)
    claimed_anniversaries: set = field(default_factory=set)
    last_teleport_time: float = 0.0

    def years_married(self, now=None):
        now = time.time() if now is None else now
        return max(0, int((now - self.marry_time) // YEAR_SECONDS))


class MarriageSystem:
    def __init__(self):
        self.marriages: list = []
        self.shared_inventory: dict = {}

    # ---------- 内部工具 ----------
    def _find_marriage(self, player):
        for marriage in self.marriages:
            if player in (marriage.husband, marriage.wife):
                return marriage
        return None

    def _is_single(self, player):
        return self._find_marriage(player) is None

    def _couple_key(self, marriage):
        return tuple(sorted((marriage.husband, marriage.wife)))

    # ---------- bug1: 求婚校验双方等级与单身状态 ----------
    def propose(self, p1, p2, level, target_level=None):
        if p1 == p2:
            return False
        if level < PROPOSE_MIN_LEVEL:
            return False
        if target_level is not None and target_level < PROPOSE_MIN_LEVEL:
            return False
        if not self._is_single(p1):
            return False
        if not self._is_single(p2):
            return False
        return True

    def marry(self, p1, p2, marry_time=None, intimacy=0,
              pre_marriage_assets=None, post_marriage_assets=None):
        if not self.propose(p1, p2, PROPOSE_MIN_LEVEL, PROPOSE_MIN_LEVEL):
            return None
        if marry_time is None:
            marry_time = time.time()
        marriage = Marriage(
            husband=p1,
            wife=p2,
            marry_time=marry_time,
            intimacy=intimacy,
            pre_marriage_assets=dict(pre_marriage_assets or {}),
            post_marriage_assets=dict(post_marriage_assets or {}),
        )
        self.marriages.append(marriage)
        return marriage

    # ---------- bug2: 婚礼奖励按档次区分 ----------
    def get_wedding_reward(self, tier):
        tier = WEDDING_TIER_ALIASES.get(tier, tier)
        reward = WEDDING_REWARDS.get(tier, WEDDING_REWARDS["normal"])
        result = dict(reward)
        result["items"] = list(reward["items"])
        return result

    # ---------- bug3: 技能概率随亲密度与婚龄提升 ----------
    def get_couple_skill_chance(self, marriage, now=None):
        intimacy = max(0, getattr(marriage, "intimacy", 0))
        intimacy_bonus = min(intimacy, SKILL_INTIMACY_CAP) / SKILL_INTIMACY_CAP * 0.3
        years_bonus = min(marriage.years_married(now), SKILL_YEARS_CAP) * 0.03
        chance = SKILL_BASE_CHANCE + intimacy_bonus + years_bonus
        return min(SKILL_MAX_CHANCE, round(chance, 4))

    # ---------- bug4: 离婚财产分割(协议/强制) ----------
    def divorce(self, proposer, marriage, forced=False):
        if isinstance(forced, str):
            forced = forced.lower() in ("forced", "强制", "强制离婚")
        if proposer not in (marriage.husband, marriage.wife):
            return None
        other = marriage.wife if proposer == marriage.husband else marriage.husband
        pre = marriage.pre_marriage_assets

        if forced:
            proposer_ratio = FORCED_DIVORCE_PROPOSER_RATIO
            other_ratio = FORCED_DIVORCE_OTHER_RATIO
        else:
            proposer_ratio = other_ratio = 0.5

        proposer_post = {}
        other_post = {}
        for asset, value in marriage.post_marriage_assets.items():
            proposer_post[asset] = value * proposer_ratio
            other_post[asset] = value * other_ratio

        result = {
            "mode": "forced" if forced else "agreement",
            "proposer_get": {
                "pre": dict(pre.get(proposer, {})),
                "post": proposer_post,
            },
            "other_get": {
                "pre": dict(pre.get(other, {})),
                "post": other_post,
            },
            proposer: {
                "pre": dict(pre.get(proposer, {})),
                "post": proposer_post,
            },
            other: {
                "pre": dict(pre.get(other, {})),
                "post": other_post,
            },
        }

        if marriage in self.marriages:
            self.marriages.remove(marriage)
        self.shared_inventory.pop(self._couple_key(marriage), None)
        return result

    # ---------- bug5: 夫妻仓库(双方存取, 额度限制) ----------
    def _warehouse(self, marriage):
        return self.shared_inventory.setdefault(self._couple_key(marriage), {})

    def warehouse_used(self, marriage):
        return sum(self._warehouse(marriage).values())

    def deposit(self, player, marriage, item, count=1):
        if player not in (marriage.husband, marriage.wife):
            return False
        if count <= 0:
            return False
        warehouse = self._warehouse(marriage)
        if self.warehouse_used(marriage) + count > WAREHOUSE_CAPACITY:
            return False
        warehouse[item] = warehouse.get(item, 0) + count
        return True

    def withdraw(self, player, marriage, item, count=1):
        if player not in (marriage.husband, marriage.wife):
            return False
        if count <= 0:
            return False
        warehouse = self._warehouse(marriage)
        if warehouse.get(item, 0) < count:
            return False
        warehouse[item] -= count
        if warehouse[item] == 0:
            del warehouse[item]
        return True

    def warehouse_balance(self, marriage, item=None):
        warehouse = self._warehouse(marriage)
        if item is None:
            return dict(warehouse)
        return warehouse.get(item, 0)

    # ---------- bug6: 纪念日奖励递增且有领取记录 ----------
    def get_anniversary_reward(self, marriage, year, now=None):
        if year is None or year < 1:
            return None
        if year > marriage.years_married(now):
            return None
        if year in marriage.claimed_anniversaries:
            return None
        marriage.claimed_anniversaries.add(year)
        return {
            "gift": "rose",
            "year": year,
            "gold": 1000 * year,
            "title": "结婚%d周年" % year,
        }

    # ---------- bug7: 夫妻传送冷却与场景限制 ----------
    def couple_teleport(self, p1, p2, scene, now=None):
        scene_name = scene.get("name") if isinstance(scene, dict) else scene
        if scene_name in TELEPORT_BANNED_SCENES:
            return False
        marriage = self._find_marriage(p1)
        if marriage is None or p2 not in (marriage.husband, marriage.wife):
            return False
        now = time.time() if now is None else now
        if now - marriage.last_teleport_time < TELEPORT_COOLDOWN:
            return False
        marriage.last_teleport_time = now
        return True

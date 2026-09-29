"""结婚系统7个bug修复测试(8个用例)"""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from marriage.system import (  # noqa: E402
    Marriage,
    MarriageSystem,
    PROPOSE_MIN_LEVEL,
    SKILL_BASE_CHANCE,
    TELEPORT_COOLDOWN,
    WAREHOUSE_CAPACITY,
    YEAR_SECONDS,
)


def make_marriage(intimacy=100, years=0, now=None, **kwargs):
    now = time.time() if now is None else now
    return Marriage(
        husband="p1",
        wife="p2",
        marry_time=now - years * YEAR_SECONDS,
        intimacy=intimacy,
        **kwargs,
    )


# bug1: 求婚同时检查双方等级与婚姻状态
class TestPropose:
    def test_married_player_cannot_propose_again(self):
        ms = MarriageSystem()
        ms.marriages = [Marriage("p1", "p2", 0, 100)]
        assert not ms.propose("p1", "p3", 50), "已婚玩家还能向他人求婚"
        assert not ms.propose("p3", "p1", 50), "向已婚玩家求婚居然成功"

    def test_both_level_and_single_required(self):
        ms = MarriageSystem()
        assert not ms.propose("p1", "p2", PROPOSE_MIN_LEVEL - 1), "等级不足可求婚"
        assert not ms.propose("p1", "p2", 50, target_level=20), "对方等级不足可求婚"
        assert ms.propose("p1", "p2", 50), "双方单身且等级达标应能求婚"
        assert ms.propose("p1", "p2", 50, target_level=40), "双方达标应能求婚"


# bug2: 婚礼奖励按档次区分, 豪华有专属称号道具
class TestWeddingReward:
    def test_wedding_tier_differs(self):
        ms = MarriageSystem()
        normal = ms.get_wedding_reward("normal")
        luxury = ms.get_wedding_reward("luxury")
        assert normal != luxury, "婚礼奖励不区分档次"
        assert luxury["gold"] > normal["gold"]
        assert luxury.get("title"), "豪华婚礼缺少专属称号"
        assert set(luxury["items"]) - set(normal["items"]), "豪华婚礼缺少专属道具"


# bug3: 技能概率随亲密度和婚龄提升
class TestCoupleSkill:
    def test_chance_grows_with_intimacy_and_years(self):
        ms = MarriageSystem()
        base = ms.get_couple_skill_chance(make_marriage(intimacy=0, years=0))
        intimate = ms.get_couple_skill_chance(make_marriage(intimacy=500, years=0))
        old = ms.get_couple_skill_chance(make_marriage(intimacy=0, years=3))
        assert base == SKILL_BASE_CHANCE
        assert intimate > base, "亲密度未提升技能概率"
        assert old > base, "婚龄未提升技能概率"
        cap = ms.get_couple_skill_chance(make_marriage(intimacy=10 ** 9, years=99))
        assert cap <= 0.8, "技能概率超过上限"


# bug4: 离婚按婚前/婚后财产分割, 协议与强制
class TestDivorce:
    def test_agreement_and_forced_split(self):
        ms = MarriageSystem()
        marriage = make_marriage(
            pre_marriage_assets={
                "p1": {"house": 1},
                "p2": {"car": 1},
            },
            post_marriage_assets={"gold": 1000},
        )
        result = ms.divorce("p1", marriage, forced=False)
        # 婚前财产各自拿回
        assert result["p1"]["pre"] == {"house": 1}
        assert result["p2"]["pre"] == {"car": 1}
        # 协议离婚婚后财产平分, 提出方不再净身出户
        assert result["p1"]["post"]["gold"] == 500
        assert result["p2"]["post"]["gold"] == 500
        assert marriage not in ms.marriages

        marriage2 = make_marriage(
            pre_marriage_assets={"p1": {}, "p2": {}},
            post_marriage_assets={"gold": 1000},
        )
        forced = ms.divorce("p1", marriage2, forced=True)
        # 强制离婚提出方少分, 但不是净身出户
        assert 0 < forced["p1"]["post"]["gold"] < forced["p2"]["post"]["gold"]


# bug5: 夫妻仓库双方可存取且有额度限制
class TestSharedWarehouse:
    def test_deposit_withdraw_and_quota(self):
        ms = MarriageSystem()
        marriage = make_marriage()
        assert ms.deposit("p1", marriage, "红药", 50)
        assert ms.deposit("p2", marriage, "蓝药", 50)
        assert not ms.deposit("p1", marriage, "红药", 1), "超过仓库额度仍可存入"
        # 双方都能取对方存的物品
        assert ms.withdraw("p2", marriage, "红药", 10)
        assert ms.warehouse_balance(marriage, "红药") == 40
        assert not ms.withdraw("p1", marriage, "蓝药", 999), "库存不足仍可取出"
        # 外人不能存取
        assert not ms.deposit("p3", marriage, "红药", 1)
        assert not ms.withdraw("p3", marriage, "蓝药", 1)


# bug6: 纪念日奖励递增且有领取记录
class TestAnniversary:
    def test_scaled_reward_and_claim_record(self):
        ms = MarriageSystem()
        now = 10_000_000
        marriage = make_marriage(years=3, now=now)
        first = ms.get_anniversary_reward(marriage, 1, now=now)
        second = ms.get_anniversary_reward(marriage, 2, now=now)
        assert first is not None and second is not None
        assert second["gold"] > first["gold"], "纪念日奖励未按婚龄递增"
        assert ms.get_anniversary_reward(marriage, 1, now=now) is None, "同一年能重复领取"
        # 未到的婚龄不能领
        assert ms.get_anniversary_reward(marriage, 4, now=now) is None


# bug7: 传送冷却与场景限制
class TestCoupleTeleport:
    def test_cooldown_and_scene_restriction(self):
        ms = MarriageSystem()
        now = 10_000_000
        marriage = make_marriage(now=now)
        ms.marriages = [marriage]
        assert ms.couple_teleport("p1", "p2", "city", now=now), "普通场景应可传送"
        assert not ms.couple_teleport("p1", "p2", "city", now=now + 10), "冷却内仍可传送"
        later = now + TELEPORT_COOLDOWN + 1
        assert ms.couple_teleport("p1", "p2", "city", now=later), "冷却结束应可传送"
        assert not ms.couple_teleport("p1", "p2", "dungeon", now=later + TELEPORT_COOLDOWN), "副本内可传送"
        assert not ms.couple_teleport("p1", "p2", "battlefield", now=later + 2 * TELEPORT_COOLDOWN), "战场内可传送"

    def test_only_spouses_can_teleport(self):
        ms = MarriageSystem()
        now = 10_000_000
        ms.marriages = [make_marriage(now=now)]
        assert not ms.couple_teleport("p1", "p3", "city", now=now), "非夫妻也能传送"
        assert not ms.couple_teleport("p9", "p8", "city", now=now), "未婚也能传送"

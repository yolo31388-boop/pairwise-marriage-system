"""结婚测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import MarriageSystem, Marriage

class TestPropose:
    def test_single_check(self):
        ms = MarriageSystem()
        ms.marriages = [Marriage("p1","p2",0,100)]
        assert not ms.propose("p1", "p3", 50), "已婚还能求婚"

class TestReward:
    def test_wedding_tier_differs(self):
        ms = MarriageSystem()
        r1 = ms.get_wedding_reward("normal")
        r2 = ms.get_wedding_reward("luxury")
        assert r2 != r1, "婚礼奖励不区分档次"

#TODO: Add test cases for slots
import pytest
from casino.games.slots.variants.expanded import payout_for_row, score_lines

def test_payout_for_row_max_value_match():
    assert payout_for_row(("D", "D", "D"), 100) == 500


def test_payout_for_row_high_value_match():
    assert payout_for_row(("A", "A", "A"), 100) == 150


def test_payout_for_row_no_bet():
    assert payout_for_row(("A", "A", "A"), 0) == 0

def test_scorelines_no_winners():
    grid = (("A", "B", "C"), ("D", "E", "F"), ("G", "H", "I"))
    line_bets = (10, 20, 30)
    total, winners = score_lines(grid, line_bets)
    assert total == 0
    assert winners == []

def test_scorelines_one_winner():
    grid = (("A", "A", "A"), ("D", "E", "F"), ("G", "H", "I"))
    line_bets = (10, 20, 30)
    total, winners = score_lines(grid, line_bets)
    assert total == 15  # 10 * 1.5
    assert winners == [0]

def test_scorelines_multiple_winners():
    grid = (("A", "A", "A"), ("D", "D", "D"), ("G", "H", "I"))
    line_bets = (10, 20, 30)
    total, winners = score_lines(grid, line_bets)
    assert total == 15 + 100  # 10 * 1.5 + 20 * 5
    assert winners == [0, 1]


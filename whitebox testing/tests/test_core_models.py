import pytest

from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.dice import Dice
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


def test_player_add_and_deduct_validations():
    p = Player("P", balance=100)

    with pytest.raises(ValueError):
        p.add_money(-1)
    with pytest.raises(ValueError):
        p.deduct_money(-1)

    p.add_money(0)
    p.deduct_money(0)
    assert p.balance == 100


def test_player_bankruptcy_boundaries():
    p1 = Player("P1", balance=1)
    p2 = Player("P2", balance=0)
    p3 = Player("P3", balance=-10)
    assert p1.is_bankrupt() is False
    assert p2.is_bankrupt() is True
    assert p3.is_bankrupt() is True


def test_player_move_wraps_and_awards_go_on_zero():
    p = Player("P", balance=100)
    p.position = 39
    p.move(1)
    assert p.position == 0
    assert p.balance > 100


def test_property_mortgage_unmortgage_cycle():
    prop = Property("X", 1, 200, 20)
    first = prop.mortgage()
    second = prop.mortgage()
    assert first == 100
    assert second == 0

    cost = prop.unmortgage()
    assert cost == 110
    assert prop.is_mortgaged is False


def test_property_group_all_owned_by_requires_full_group_ownership():
    group = PropertyGroup("G", "c")
    p1 = Player("P1")
    p2 = Player("P2")
    a = Property("A", 1, 100, 10, group)
    b = Property("B", 3, 100, 10, group)

    a.owner = p1
    b.owner = p2

    assert group.all_owned_by(p1) is False


def test_bank_pay_out_paths():
    bank = Bank()
    start = bank.get_balance()

    assert bank.pay_out(0) == 0
    assert bank.pay_out(-5) == 0
    assert bank.get_balance() == start

    with pytest.raises(ValueError):
        bank.pay_out(start + 1)

    paid = bank.pay_out(10)
    assert paid == 10
    assert bank.get_balance() == start - 10


def test_bank_collect_ignores_negative_amounts():
    bank = Bank()
    start = bank.get_balance()
    bank.collect(-100)
    assert bank.get_balance() == start


def test_bank_give_loan_only_for_positive_amount():
    bank = Bank()
    p = Player("P", balance=100)
    bank.give_loan(p, 0)
    bank.give_loan(p, -5)
    assert bank.loan_count() == 0

    bank.give_loan(p, 200)
    assert bank.loan_count() == 1
    assert p.balance == 300


def test_board_tile_and_purchasable_paths():
    board = Board()
    assert board.get_tile_type(30) == "go_to_jail"
    assert board.get_tile_type(1) == "property"

    free_pos = 12
    assert board.get_tile_type(free_pos) == "blank"

    prop = board.get_property_at(1)
    assert board.is_purchasable(12) is False

    prop.is_mortgaged = True
    assert board.is_purchasable(1) is False

    prop.is_mortgaged = False
    prop.owner = Player("Owner")
    assert board.is_purchasable(1) is False

    prop.owner = None
    assert board.is_purchasable(1) is True


def test_dice_roll_updates_streak(monkeypatch):
    d = Dice()
    sequence = iter([3, 3, 2, 5])
    monkeypatch.setattr("random.randint", lambda a, b: next(sequence))

    first_total = d.roll()
    assert first_total == 6
    assert d.doubles_streak == 1

    second_total = d.roll()
    assert second_total == 7
    assert d.doubles_streak == 0


def test_dice_roll_uses_six_sided_range(monkeypatch):
    d = Dice()

    def strict_randint(low, high):
        assert low == 1
        assert high == 6
        return 6

    monkeypatch.setattr("random.randint", strict_randint)
    total = d.roll()
    assert total == 12


def test_card_deck_empty_and_cycle():
    empty = CardDeck([])
    assert empty.draw() is None
    assert empty.peek() is None

    cards = [{"id": 1}, {"id": 2}]
    deck = CardDeck(cards)
    assert deck.draw()["id"] == 1
    assert deck.draw()["id"] == 2
    assert deck.draw()["id"] == 1


def test_card_deck_cards_remaining_reaches_zero_after_full_draw_cycle():
    deck = CardDeck([{"id": 1}, {"id": 2}])
    assert deck.cards_remaining() == 2
    deck.draw()
    assert deck.cards_remaining() == 1
    deck.draw()
    assert deck.cards_remaining() == 0

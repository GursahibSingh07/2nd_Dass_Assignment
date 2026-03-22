import builtins

import pytest

from moneypoly.config import GO_SALARY, INCOME_TAX_AMOUNT, JAIL_FINE, LUXURY_TAX_AMOUNT
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property


class DiceStub:
    def __init__(self, total=7, doubles=False, streak=0):
        self._total = total
        self._doubles = doubles
        self.doubles_streak = streak

    def roll(self):
        return self._total

    def is_doubles(self):
        return self._doubles

    def describe(self):
        return "stub"


def test_play_turn_jailed_player_path(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()
    p.in_jail = True

    called = {"jail": 0, "advance": 0}
    monkeypatch.setattr(g, "_handle_jail_turn", lambda player: called.__setitem__("jail", called["jail"] + 1))
    monkeypatch.setattr(g, "advance_turn", lambda: called.__setitem__("advance", called["advance"] + 1))

    g.play_turn()

    assert called["jail"] == 1
    assert called["advance"] == 1


def test_play_turn_triple_doubles_sends_to_jail(game_two_players):
    g = game_two_players
    p = g.current_player()
    g.dice = DiceStub(total=8, doubles=True, streak=3)

    g.play_turn()

    assert p.in_jail is True


def test_play_turn_extra_turn_on_doubles(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()
    g.dice = DiceStub(total=6, doubles=True, streak=1)

    moved = {"called": 0}
    monkeypatch.setattr(g, "_move_and_resolve", lambda player, steps: moved.__setitem__("called", moved["called"] + 1))

    before_turn = g.turn_number
    before_idx = g.current_index
    g.play_turn()

    assert moved["called"] == 1
    assert g.turn_number == before_turn
    assert g.current_index == before_idx
    assert g.current_player() == p


@pytest.mark.parametrize(
    "tile, expected_delta, expected_bank_delta",
    [
        ("income_tax", -INCOME_TAX_AMOUNT, INCOME_TAX_AMOUNT),
        ("luxury_tax", -LUXURY_TAX_AMOUNT, LUXURY_TAX_AMOUNT),
    ],
)
def test_move_and_resolve_tax_tiles(game_two_players, monkeypatch, tile, expected_delta, expected_bank_delta):
    g = game_two_players
    p = g.current_player()
    p.balance = 1000
    start_bank = g.bank.get_balance()

    monkeypatch.setattr(p, "move", lambda steps: 4)
    p.position = 4
    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: tile)

    g._move_and_resolve(p, 4)

    assert p.balance == 1000 + expected_delta
    assert g.bank.get_balance() == start_bank + expected_bank_delta


def test_move_and_resolve_go_to_jail(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()

    monkeypatch.setattr(p, "move", lambda steps: 30)
    p.position = 30
    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "go_to_jail")

    g._move_and_resolve(p, 1)
    assert p.in_jail is True


def test_handle_property_tile_buy_auction_skip(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()
    prop = Property("X", 1, 60, 2)

    calls = {"buy": 0, "auction": 0}
    monkeypatch.setattr(g, "buy_property", lambda player, item: calls.__setitem__("buy", calls["buy"] + 1))
    monkeypatch.setattr(g, "auction_property", lambda item: calls.__setitem__("auction", calls["auction"] + 1))

    monkeypatch.setattr(builtins, "input", lambda _prompt: "b")
    g._handle_property_tile(p, prop)

    monkeypatch.setattr(builtins, "input", lambda _prompt: "a")
    g._handle_property_tile(p, prop)

    monkeypatch.setattr(builtins, "input", lambda _prompt: "s")
    g._handle_property_tile(p, prop)

    assert calls["buy"] == 1
    assert calls["auction"] == 1


def test_buy_property_success_and_failure(game_two_players):
    g = game_two_players
    p = g.current_player()
    prop = Property("Y", 3, 100, 10)

    p.balance = 90
    assert g.buy_property(p, prop) is False
    assert prop.owner is None

    p.balance = 150
    assert g.buy_property(p, prop) is True
    assert prop.owner == p


def test_buy_property_allows_exact_balance(game_two_players):
    g = game_two_players
    p = g.current_player()
    prop = Property("Exact", 12, 200, 16)

    p.balance = prop.price
    assert g.buy_property(p, prop) is True
    assert prop.owner == p


def test_pay_rent_paths(game_two_players):
    g = game_two_players
    payer = g.players[0]
    owner = g.players[1]
    prop = Property("Z", 6, 120, 8)

    prop.owner = owner
    prop.is_mortgaged = True
    start = payer.balance
    g.pay_rent(payer, prop)
    assert payer.balance == start

    prop.is_mortgaged = False
    prop.owner = None
    g.pay_rent(payer, prop)
    assert payer.balance == start

    prop.owner = owner
    g.pay_rent(payer, prop)
    assert payer.balance == start - prop.base_rent


def test_mortgage_and_unmortgage_paths(game_two_players):
    g = game_two_players
    p = g.current_player()
    other = g.players[1]
    prop = Property("M", 8, 200, 20)

    prop.owner = other
    assert g.mortgage_property(p, prop) is False

    prop.owner = p
    assert g.mortgage_property(p, prop) is True
    assert prop.is_mortgaged is True

    assert g.mortgage_property(p, prop) is False

    assert g.unmortgage_property(other, prop) is False

    p.balance = 0
    assert g.unmortgage_property(p, prop) is False
    assert prop.is_mortgaged is True

    p.balance = 1000
    assert g.unmortgage_property(p, prop) is True
    assert prop.is_mortgaged is False


def test_trade_paths(game_two_players):
    g = game_two_players
    seller, buyer = g.players
    prop = Property("T", 9, 220, 18)

    assert g.trade(seller, buyer, prop, 50) is False

    prop.owner = seller
    seller.add_property(prop)

    buyer.balance = 10
    assert g.trade(seller, buyer, prop, 20) is False

    buyer.balance = 20
    assert g.trade(seller, buyer, prop, 20) is True
    assert prop.owner == buyer


def test_trade_rejects_non_positive_cash_amounts(game_two_players):
    g = game_two_players
    seller, buyer = g.players
    prop = Property("NoFree", 26, 260, 22)
    prop.owner = seller
    seller.add_property(prop)

    assert g.trade(seller, buyer, prop, 0) is False

    assert g.trade(seller, buyer, prop, -10) is False


def test_auction_paths(game_two_players, monkeypatch):
    g = game_two_players
    prop = Property("Auc", 11, 140, 10)

    seq = iter([0, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g.auction_property(prop)
    assert prop.owner is None

    seq = iter([5, 20])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g.auction_property(prop)
    assert prop.owner is not None


def test_handle_jail_turn_paths(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()
    p.in_jail = True

    p.get_out_of_jail_cards = 1
    confirms = iter([True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda prompt: next(confirms))
    monkeypatch.setattr(g.dice, "roll", lambda: 4)
    monkeypatch.setattr(g.dice, "describe", lambda: "2 + 2")
    monkeypatch.setattr(g, "_move_and_resolve", lambda player, steps: None)
    g._handle_jail_turn(p)
    assert p.in_jail is False
    assert p.get_out_of_jail_cards == 0

    p.in_jail = True
    p.jail_turns = 1
    p.get_out_of_jail_cards = 0
    confirms = iter([True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda prompt: next(confirms))
    g._handle_jail_turn(p)
    assert p.in_jail is False

    p.in_jail = True
    p.jail_turns = 2
    p.balance = 100
    confirms = iter([False])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda prompt: next(confirms))
    g._handle_jail_turn(p)
    assert p.in_jail is False
    assert p.balance == 100 - JAIL_FINE


def test_apply_card_paths(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()
    other = g.players[1]

    start = p.balance
    g._apply_card(p, None)
    assert p.balance == start

    g._apply_card(p, {"description": "collect", "action": "collect", "value": 10})
    assert p.balance == start + 10

    g._apply_card(p, {"description": "pay", "action": "pay", "value": 5})
    assert p.balance == start + 5

    g._apply_card(p, {"description": "jail", "action": "jail", "value": 0})
    assert p.in_jail is True

    cards_before = p.get_out_of_jail_cards
    g._apply_card(p, {"description": "jf", "action": "jail_free", "value": 0})
    assert p.get_out_of_jail_cards == cards_before + 1

    p.position = 35
    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "blank")
    g._apply_card(p, {"description": "go", "action": "move_to", "value": 0})
    assert p.position == 0
    assert p.balance >= start + 5 + GO_SALARY

    p.balance = 100
    other.balance = 20
    g._apply_card(p, {"description": "birthday", "action": "birthday", "value": 10})
    assert p.balance == 110
    assert other.balance == 10


def test_check_bankruptcy_and_find_winner(game_two_players):
    g = game_two_players
    p1, p2 = g.players

    prop = Property("Owned", 15, 180, 14)
    prop.owner = p1
    prop.is_mortgaged = True
    p1.add_property(prop)

    p1.balance = 0
    g._check_bankruptcy(p1)
    assert p1.is_eliminated is True
    assert p1 not in g.players
    assert prop.owner is None
    assert prop.is_mortgaged is False

    p2.balance = 200
    p3 = Player("Charlie", balance=50)
    g.players.append(p3)
    assert g.find_winner() == p2


def test_game_requires_minimum_two_players():
    with pytest.raises(ValueError):
        Game([])

    with pytest.raises(ValueError):
        Game(["Solo"])


def test_interactive_menu_and_submenus(game_two_players, monkeypatch):
    g = game_two_players
    player = g.current_player()
    other = g.players[1]

    calls = {"mortgage": 0, "unmortgage": 0, "trade": 0, "loan": 0}
    monkeypatch.setattr(g, "_menu_mortgage", lambda p: calls.__setitem__("mortgage", calls["mortgage"] + 1))
    monkeypatch.setattr(g, "_menu_unmortgage", lambda p: calls.__setitem__("unmortgage", calls["unmortgage"] + 1))
    monkeypatch.setattr(g, "_menu_trade", lambda p: calls.__setitem__("trade", calls["trade"] + 1))
    monkeypatch.setattr(g.bank, "give_loan", lambda p, amt: calls.__setitem__("loan", calls["loan"] + 1))

    seq = iter([3, 4, 5, 6, 0, 6, 25, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g.interactive_menu(player)

    assert calls["mortgage"] == 1
    assert calls["unmortgage"] == 1
    assert calls["trade"] == 1
    assert calls["loan"] == 1

    g.players = [player]
    g._menu_trade(player)

    g.players = [player, other]
    seq = iter([99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(player)

    seq = iter([1])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(player)

    prop = Property("Tradeable", 16, 180, 14)
    prop.owner = player
    player.properties = [prop]

    seq = iter([1, 99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(player)


def test_menu_mortgage_and_unmortgage_edges(game_two_players, monkeypatch):
    g = game_two_players
    p = g.current_player()

    g._menu_mortgage(p)
    g._menu_unmortgage(p)

    prop = Property("Menu", 19, 200, 16)
    prop.owner = p
    p.properties = [prop]

    seq = iter([99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_mortgage(p)

    prop.is_mortgaged = True
    seq = iter([99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_unmortgage(p)


def test_player_gets_salary_when_passing_go():
    p = Player("PassGo", balance=100)
    p.position = 39
    p.move(2)
    assert p.position == 1
    assert p.balance == 100 + GO_SALARY

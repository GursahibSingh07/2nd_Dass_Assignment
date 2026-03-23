import builtins

import pytest

from moneypoly.bank import Bank
from moneypoly.cards import CardDeck
from moneypoly.dice import Dice
from moneypoly.board import Board
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup, PropertyTerms
from moneypoly import ui


def test_ui_paths(capsys, monkeypatch):
    p = Player("UI", balance=123)
    board = Board()

    ui.print_banner("HELLO")
    p.in_jail = False
    p.get_out_of_jail_cards = 0
    p.properties = []
    ui.print_player_card(p)

    p.in_jail = True
    p.get_out_of_jail_cards = 1
    prop = board.get_property_at(1)
    prop.owner = p
    p.properties = [prop]
    ui.print_player_card(p)

    ui.print_standings([p])
    ui.print_board_ownership(board)
    assert ui.format_currency(1500) == "$1,500"

    monkeypatch.setattr(builtins, "input", lambda _prompt: "42")
    assert ui.safe_int_input("x") == 42

    monkeypatch.setattr(builtins, "input", lambda _prompt: "not-int")
    assert ui.safe_int_input("x", default=9) == 9

    monkeypatch.setattr(builtins, "input", lambda _prompt: "y")
    assert ui.confirm("c") is True

    monkeypatch.setattr(builtins, "input", lambda _prompt: "N")
    assert ui.confirm("c") is False

    out = capsys.readouterr().out
    assert "HELLO" in out


def test_board_property_bank_cards_dice_extra_paths(monkeypatch, capsys):
    board = Board()
    player = Player("P")

    assert board.is_special_tile(0) is True
    assert board.is_special_tile(12) is False
    assert isinstance(board.unowned_properties(), list)
    assert "Board(" in repr(board)

    prop = board.get_property_at(1)
    prop.owner = player
    owned = board.properties_owned_by(player)
    assert prop in owned

    bank = Bank()
    bank.give_loan(player, 10)
    assert bank.total_loans_issued() >= 10
    bank.summary()
    assert "Bank(" in repr(bank)

    deck = CardDeck([{"id": 1}, {"id": 2}])
    assert deck.peek()["id"] == 1
    monkeypatch.setattr("random.shuffle", lambda arr: arr.reverse())
    deck.reshuffle()
    assert deck.cards_remaining() == 2
    assert len(deck) == 2
    assert "CardDeck(" in repr(deck)

    d = Dice()
    d.reset()
    d.die1 = 2
    d.die2 = 3
    assert "=" in d.describe()
    assert "Dice(" in repr(d)

    out = capsys.readouterr().out
    assert "Bank reserves" in out


def test_player_and_property_group_remaining_paths():
    p = Player("A")
    q = Player("B")

    p.move(2)
    assert p.position == 2

    prop = Property("One", 1, PropertyTerms(100, 10))
    p.add_property(prop)
    p.add_property(prop)
    assert p.count_properties() == 1
    p.remove_property(prop)
    p.remove_property(prop)
    assert p.count_properties() == 0

    _ = p.status_line()
    _ = repr(p)

    g = PropertyGroup("G", "c")
    p1 = Property("P1", 1, PropertyTerms(100, 10), g)
    p2 = Property("P2", 2, PropertyTerms(100, 10), g)

    g.add_property(p1)
    p3 = Property("P3", 3, PropertyTerms(120, 12))
    g.add_property(p3)

    p1.owner = p
    p2.owner = q

    assert p1.get_rent() == 10
    p1.is_mortgaged = True
    assert p1.get_rent() == 0
    p1.is_mortgaged = False

    assert p1.is_available() is False
    p1.owner = None
    assert p1.is_available() is True

    assert g.all_owned_by(None) is False
    counts = g.get_owner_counts()
    assert isinstance(counts, dict)
    assert g.size() >= 2
    assert "PropertyGroup(" in repr(g)
    assert "Property(" in repr(p1)


class DicePathStub:
    def __init__(self, total=5, doubles=False, streak=0):
        self._total = total
        self._doubles = doubles
        self.doubles_streak = streak

    def roll(self):
        return self._total

    def is_doubles(self):
        return self._doubles

    def describe(self):
        return "stub"


def test_game_remaining_branches(monkeypatch):
    g = Game(["A", "B"])
    p = g.current_player()

    g.dice = DicePathStub(total=3, doubles=False, streak=0)
    monkeypatch.setattr(g, "_move_and_resolve", lambda player, steps: None)
    idx_before = g.current_index
    g.play_turn()
    assert g.current_index != idx_before
    monkeypatch.setattr(g, "_move_and_resolve", Game._move_and_resolve.__get__(g, Game))

    p = g.current_player()
    monkeypatch.setattr(p, "move", lambda steps: 7)
    p.position = 7

    called = {"card": 0, "tile": 0}
    monkeypatch.setattr(g, "_apply_card", lambda player, card: called.__setitem__("card", called["card"] + 1))
    monkeypatch.setattr(g, "_handle_property_tile", lambda player, prop: called.__setitem__("tile", called["tile"] + 1))

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "free_parking")
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "chance")
    monkeypatch.setattr(g.chance_deck, "draw", lambda: {"action": "collect", "value": 1, "description": "d"})
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "community_chest")
    monkeypatch.setattr(g.community_deck, "draw", lambda: {"action": "pay", "value": 1, "description": "d"})
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "railroad")
    monkeypatch.setattr(g.board, "get_property_at", lambda pos: None)
    g._move_and_resolve(p, 1)

    rr = Property("RR", 5, PropertyTerms(200, 25))
    monkeypatch.setattr(g.board, "get_property_at", lambda pos: rr)
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "property")
    monkeypatch.setattr(g.board, "get_property_at", lambda pos: None)
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_property_at", lambda pos: Property("P", 1, PropertyTerms(100, 10)))
    g._move_and_resolve(p, 1)

    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "blank")
    g._move_and_resolve(p, 1)

    assert called["card"] >= 2
    assert called["tile"] >= 2
    monkeypatch.setattr(g, "_handle_property_tile", Game._handle_property_tile.__get__(g, Game))
    monkeypatch.setattr(g, "_apply_card", Game._apply_card.__get__(g, Game))

    prop = Property("Own", 1, PropertyTerms(100, 10))
    prop.owner = p
    g._handle_property_tile(p, prop)

    pay_called = {"v": 0}
    prop.owner = g.players[0] if g.players[0] != p else g.players[1]
    monkeypatch.setattr(g, "pay_rent", lambda payer, pr: pay_called.__setitem__("v", pay_called["v"] + 1))
    g._handle_property_tile(p, prop)
    assert pay_called["v"] == 1

    prop2 = Property("U", 2, PropertyTerms(100, 10))
    prop2.owner = p
    assert g.unmortgage_property(p, prop2) is False

    g.players[0].balance = 10
    g.players[1].balance = 10
    seq = iter([100, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g.auction_property(Property("AUC", 3, PropertyTerms(100, 10)))

    p.in_jail = True
    p.get_out_of_jail_cards = 1
    p.jail_turns = 0
    confirms = iter([False, True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda prompt: next(confirms))
    monkeypatch.setattr(g.dice, "roll", lambda: 2)
    monkeypatch.setattr(g.dice, "describe", lambda: "1+1")
    monkeypatch.setattr(g, "_move_and_resolve", lambda player, steps: None)
    g._handle_jail_turn(p)

    p.in_jail = True
    p.get_out_of_jail_cards = 0
    p.jail_turns = 0
    confirms = iter([False])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda prompt: next(confirms))
    g._handle_jail_turn(p)
    assert p.in_jail is True and p.jail_turns == 1

    p.balance = 100
    for other in g.players:
        if other != p:
            other.balance = 0
    g._apply_card(p, {"description": "x", "action": "collect_from_all", "value": 10})
    g._apply_card(p, {"description": "noop", "action": "unknown", "value": 0})

    target = Property("Target", 8, PropertyTerms(120, 8))
    called_tile = {"n": 0}
    monkeypatch.setattr(g.board, "get_tile_type", lambda pos: "property")
    monkeypatch.setattr(g.board, "get_property_at", lambda pos: target)
    monkeypatch.setattr(g, "_handle_property_tile", lambda player, prop: called_tile.__setitem__("n", called_tile["n"] + 1))
    p.position = 1
    g._apply_card_move_to(p, 8)
    assert called_tile["n"] == 1
    monkeypatch.setattr(g.board, "get_property_at", lambda pos: None)
    g._apply_card_move_to(p, 8)

    outsider = Player("X", balance=0)
    outsider.properties = []
    g.current_index = len(g.players)
    g._check_bankruptcy(outsider)

    g.players = []
    assert g.find_winner() is None


def test_game_run_and_menu_specific_branches(monkeypatch):
    g = Game(["A", "B"])
    steps = {"n": 0}

    def fake_play_turn():
        steps["n"] += 1
        g.running = False

    monkeypatch.setattr(g, "play_turn", fake_play_turn)
    monkeypatch.setattr("moneypoly.ui.print_banner", lambda _title: None)
    monkeypatch.setattr("moneypoly.ui.print_standings", lambda _players: None)
    monkeypatch.setattr(g, "find_winner", lambda: g.players[0])
    g.run()

    g2 = Game(["A", "B"])
    g2.running = False
    monkeypatch.setattr(g2, "find_winner", lambda: None)
    g2.run()

    g3 = Game(["SoloA", "SoloB"])
    g3.players = [g3.players[0]]
    monkeypatch.setattr(g3, "find_winner", lambda: g3.players[0])
    g3.run()

    p = g.current_player()
    seq = iter([1, 2, 6, 0, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    monkeypatch.setattr("moneypoly.ui.print_standings", lambda _players: None)
    monkeypatch.setattr("moneypoly.ui.print_board_ownership", lambda _board: None)
    g.interactive_menu(p)

    seq = iter([9, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g.interactive_menu(p)

    prop_m = Property("M", 1, PropertyTerms(100, 10))
    prop_m.owner = p
    prop_m.is_mortgaged = False
    p.properties = [prop_m]
    seq = iter([1])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    called_m = {"n": 0}
    monkeypatch.setattr(g, "mortgage_property", lambda player, prop: called_m.__setitem__("n", called_m["n"] + 1))
    g._menu_mortgage(p)
    assert called_m["n"] == 1

    prop_u = Property("U", 2, PropertyTerms(100, 10))
    prop_u.owner = p
    prop_u.is_mortgaged = True
    p.properties = [prop_u]
    seq = iter([1])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    called_u = {"n": 0}
    monkeypatch.setattr(g, "unmortgage_property", lambda player, prop: called_u.__setitem__("n", called_u["n"] + 1))
    g._menu_unmortgage(p)
    assert called_u["n"] == 1

    partner = Player("P2")
    g.players = [p, partner]
    prop_t = Property("T", 3, PropertyTerms(100, 10))
    prop_t.owner = p
    p.properties = [prop_t]
    seq = iter([1, 1, 25])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    called_t = {"n": 0}
    monkeypatch.setattr(g, "trade", lambda seller, buyer, prop, cash: called_t.__setitem__("n", called_t["n"] + 1))
    g._menu_trade(p)
    assert called_t["n"] == 1

    g.players = [p]
    g._menu_trade(p)

    g.players = [p, partner]
    seq = iter([99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(p)

    p.properties = []
    seq = iter([1])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(p)

    p.properties = [prop_t]
    seq = iter([1, 99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda prompt, default=0: next(seq))
    g._menu_trade(p)

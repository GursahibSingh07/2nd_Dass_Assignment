# Executed Test Report

## Run Summary
- Command: `./.venv/bin/python -m pytest -q`
- Result: `39 passed`
- Total tests: `39`

All previously identified logic errors have been fixed and validated by tests.

---

## Implemented Test Cases and Purpose

### `tests/test_core_models.py`

1. `test_player_add_and_deduct_validations`  
   Ensures invalid negative money operations are rejected, while zero-value operations do not cause issues.

2. `test_player_bankruptcy_boundaries`  
   Checks how bankruptcy behaves at key boundaries (`1`, `0`, negative values).

3. `test_player_move_wraps_and_awards_go_on_zero`  
   Verifies correct board wrapping and GO reward when landing exactly on position 0.

4. `test_property_mortgage_unmortgage_cycle`  
   Covers the normal mortgage → unmortgage flow and validates cost handling.

5. `test_property_group_all_owned_by_requires_full_group_ownership`  
   Ensures full ownership of a group is required. This test exposed a flaw in the current logic.

6. `test_bank_pay_out_paths`  
   Covers payout behavior for zero, negative, insufficient funds, and valid payouts.

7. `test_bank_collect_ignores_negative_amounts`  
   Checks that negative amounts are ignored, as stated in the documentation.

8. `test_bank_give_loan_only_for_positive_amount`  
   Ensures loans are only issued for valid positive amounts.

9. `test_board_tile_and_purchasable_paths`  
   Verifies tile classification and purchasable conditions across different states.

10. `test_dice_roll_updates_streak`  
    Confirms doubles correctly increment or reset the streak.

11. `test_dice_roll_uses_six_sided_range`  
    Validates that dice follow a standard 1–6 range.

12. `test_card_deck_empty_and_cycle`  
    Covers empty deck behavior and ensures drawing cycles correctly.

13. `test_card_deck_cards_remaining_reaches_zero_after_full_draw_cycle`  
    Checks how `cards_remaining()` behaves after a full cycle.

---

### `tests/test_game_logic.py`

14. `test_play_turn_jailed_player_path`  
    Covers the jailed-player flow and ensures the turn still advances.

15. `test_play_turn_triple_doubles_sends_to_jail`  
    Verifies the triple-doubles rule.

16. `test_play_turn_extra_turn_on_doubles`  
    Ensures doubles correctly grant an extra turn.

17. `test_move_and_resolve_tax_tiles[income_tax]`  
    Checks income tax deduction and bank collection.

18. `test_move_and_resolve_tax_tiles[luxury_tax]`  
    Same as above, for luxury tax.

19. `test_move_and_resolve_go_to_jail`  
    Verifies go-to-jail tile behavior.

20. `test_handle_property_tile_buy_auction_skip`  
    Covers all possible choices on unowned property (buy, auction, skip).

21. `test_buy_property_success_and_failure`  
    Checks both insufficient funds and successful purchase cases.

22. `test_buy_property_allows_exact_balance`  
    Ensures a player can buy a property when balance equals price.

23. `test_pay_rent_paths`  
    Covers both no-rent conditions and normal rent flow.

24. `test_mortgage_and_unmortgage_paths`  
    Tests ownership checks, affordability, and state transitions.

25. `test_trade_paths`  
    Verifies trade behavior including invalid ownership and successful transfer.

26. `test_trade_rejects_non_positive_cash_amounts`  
    Ensures trades require a positive cash amount.

27. `test_auction_paths`  
    Covers both no-bid and valid winning bid scenarios.

28. `test_handle_jail_turn_paths`  
    Covers all jail exit options.

29. `test_apply_card_paths`  
    Exercises major card actions and resulting state changes.

30. `test_check_bankruptcy_and_find_winner`  
    Verifies elimination logic and correct winner selection.

31. `test_game_requires_minimum_two_players`  
    Ensures invalid player counts are rejected.

32. `test_interactive_menu_and_submenus`  
    Covers menu routing and user input paths.

33. `test_menu_mortgage_and_unmortgage_edges`  
    Handles submenu edge cases such as invalid selections.

34. `test_player_gets_salary_when_passing_go`  
    Checks that salary is awarded when passing GO, not just landing on it.

---

### `tests/test_branch_completion.py`

35. `test_ui_paths`  
    Covers UI helper functions and input fallback behavior.

36. `test_board_property_bank_cards_dice_extra_paths`  
    Exercises remaining utility paths such as `repr`, summaries, and resets.

37. `test_player_and_property_group_remaining_paths`  
    Covers remaining player/property/group branches and safety checks.

38. `test_game_remaining_branches`  
    Triggers leftover game branches like blank tiles and unknown card actions.

39. `test_game_run_and_menu_specific_branches`  
    Covers end conditions in `run()` and additional menu loops.

---

## Resolved Errors and Fixes

Error #1 `test_property_group_all_owned_by_requires_full_group_ownership`
- Issue: group ownership was being treated as true even when only part of the group was owned.
- Fixes made: updated `PropertyGroup.all_owned_by` to use `all(...)` instead of `any(...)` in `moneypoly/moneypoly/property.py`.

Error #2 `test_bank_collect_ignores_negative_amounts`
- Issue: calling `Bank.collect()` with a negative value reduced the bank’s balance.
- Fixes made: added a guard (`if amount < 0: return`) so negative inputs are ignored in `moneypoly/moneypoly/bank.py`.

Error #3 `test_dice_roll_uses_six_sided_range`
- Issue: dice were effectively five-sided because the upper bound was set to 5.
- Fixes made: corrected the range to `random.randint(1, 6)` in `moneypoly/moneypoly/dice.py`.

Error #4 `test_card_deck_cards_remaining_reaches_zero_after_full_draw_cycle`
- Issue: `cards_remaining()` reset immediately after one full cycle instead of reaching zero.
- Fixes made: adjusted the logic to return the remaining count before the first cycle completes using `max(len(self.cards) - self.index, 0)` in `moneypoly/moneypoly/cards.py`.

Error #5 `test_buy_property_allows_exact_balance`
- Issue: players couldn’t buy a property when their balance exactly matched the price.
- Fixes made: changed the affordability check from `<=` to `<` in `moneypoly/moneypoly/game.py`.

Error #6 `test_mortgage_and_unmortgage_paths`
- Issue: the property state was being changed before confirming the player could afford the unmortgage cost.
- Fixes made: reordered the logic so balance and state checks happen first, and `prop.unmortgage()` is only called after validation in `moneypoly/moneypoly/game.py`.

Error #7 `test_trade_rejects_non_positive_cash_amounts`
- Issue: trades were going through even when the cash amount was zero or negative.
- Fixes made: added a validation check for `cash_amount <= 0` in `moneypoly/moneypoly/game.py`.

Error #8 `test_check_bankruptcy_and_find_winner`
- Issue: the game was selecting the player with the lowest net worth as the winner.
- Fixes made: replaced `min(...)` with `max(...)` when determining the winner in `moneypoly/moneypoly/game.py`.

Error #9 `test_game_requires_minimum_two_players`
- Issue: the game could start with fewer than two players.
- Fixes made: added a validation step in `Game.__init__` to raise a `ValueError` if fewer than two players are provided.

Error #10 `test_player_gets_salary_when_passing_go`
- Issue: players only received salary when landing exactly on GO, not when passing it.
- Fixes made: updated `Player.move()` so salary is awarded whenever the player passes or lands on GO.

---

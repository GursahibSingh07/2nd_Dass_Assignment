## Iteration 1 : 

### board.py
- Added module docstring (line 1)
- Removed redundant `== True` comparison (line 114)

### main.py
- Added module docstring (line 1)
- Added function docstring (line 11)
- Added function docstring (line 19)

### config.py
- Added module docstring (line 1)
- Specified exception type in `except` block (line 77)

### cards.py
- Added module docstring (line 1)
- Fixed `line-too-long` issues (lines 4-30)

### property.py
- Added module docustring (line 1)
- Disabled `too-many-instance` attritube issue (line 4)
- Disabled `too-many-arguements` issue (line 9)
- Removed unecessary `else` after `return` (line 41)
- Added missing final newline (line 88)


(The reason I decided to disable the issue rather than refactoring was the fact that it would have required a lot of refactoring in other files like board.py which had already gotten a perfect score. As the violation in this case was not that severe 9/7 and 6/5 and the code is rather simplistic in logic, this solution was deemed more appropriate)

### game.py
- Added module docstring (line 1)
- Removed unused `import os` and `GO_TO_JAIL_POSITION`
- Removed unnecessary parentheses in `not (0 <= idx < len(others))` and `not (0 <= pidx < ...)`
- Changed `f"GAME OVER"` to `"GAME OVER"` since there's nothing to interpolate (line 372)
- Removed `el` from `elif` after `break` in `interactive_menu` (line 395)
- Merged identical `birthday` and `collect_from_all` branches into `elif action in (...)` and extracted `move_to` logic into `_apply_card_move_to` helper to reduce branch count in `_apply_card`
- Added `# pylint: disable=too-many-instance-attributes` on `Game` class since all 9 attributes are needed (line 20)
- Added missing final newline (line 468)

### dice.py
- Added module docustring (line 1)
- Removed unused `BOARD_SIZE` import.
- Moved `self.doubles_streak = 0` into `__init__` directly instead of relying on `reset()` to define it. `reset()` still resets all three values, but pylint requires every attribute to be declared in `__init__` first.

### bank.py
- Added module docstring (line 1)
- Added class docstring to `Bank` (line 6)
- Removed unused `import math`

### player.py
- Added module docstring (line 1)
- Removed unused `import sys`
- Removed unused `old_position` variable in `move()`
- Added `# pylint: disable=too-many-instance-attributes` on `Player` class since all 8 attributes are genuine game state (line 5)
---


## Iteration 2 :

### property.py
- Refactored the constructor to use a `PropertyTerms` dataclass instead of passing raw `price` and `base_rent` values  
- Replaced direct instance attributes (`owner`, `is_mortgaged`, `houses`) with an internal `_state` dictionary and property accessors to reduce attribute count  
- Added missing docstrings for ownership, mortgage, and house-related accessors  
- Removed the previous `too-many-instance-attributes` and `too-many-arguments` pylint suppressions after refactoring  

### board.py
- Updated all `Property(...)` calls to match the new `PropertyTerms(price, rent)` structure  
- Adjusted imports to include `PropertyTerms`  

### game.py
- Moved turn-tracking into an internal `_turn` dictionary with accessors for `current_index`, `turn_number`, and `running`  
- Removed the `too-many-instance-attributes` suppression by consolidating turn-related state  
- Updated `advance_turn()` and `_check_bankruptcy()` to work directly with `_turn` internals to keep attribute count consistent  

### player.py
- Grouped jail-related state into an internal `_jail` dictionary with documented accessors  
- Removed the `too-many-instance-attributes` suppression by consolidating jail state  
- Updated `go_to_jail()` to modify `_jail` directly for consistency  
---

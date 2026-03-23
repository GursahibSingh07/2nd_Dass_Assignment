# DASS Assignment 2 - Run Guide

This workspace has 3 modules:
- `blackbox/`
- `intergration testing/`
- `whitebox testing/`

## Prerequisites

- Python 3.10+
- `pytest`
- `requests` (needed for blackbox tests)

Install (if needed):

```bash
python3 -m pip install pytest requests
```

## 1) Blackbox Module

Path: `blackbox/`

### Run tests

These tests call a running QuickCart API at `http://localhost:8080/api/v1`.
Start that API first, then run:

```bash
cd blackbox
pytest -q tests/test_quickcart.py
```

### Run code

This module is test-only and validates an external running API.

## 2) Integration Testing Module

Path: `intergration testing/`

### Run tests

```bash
cd "intergration testing"
PYTHONPATH='.' pytest -q
```

### Run code

Run the integration demo from `Code/main.py`:

```bash
cd "intergration testing"
PYTHONPATH='.' python3 -m Code.main
```

## 3) Whitebox Testing Module

Path: `whitebox testing/`

### Run tests

```bash
cd "whitebox testing"
pytest -q
```

### Run code

Run the MoneyPoly game:

```bash
cd "whitebox testing"
PYTHONPATH='Code' python3 Code/main.py
```

Then enter player names when prompted (for example: `Alice,Bob`).

## Code Access

### SSH : 
git@github.com:GursahibSingh07/2nd_Dass_Assignment.git

### HTTPS : 
https://github.com/GursahibSingh07/2nd_Dass_Assignment.git

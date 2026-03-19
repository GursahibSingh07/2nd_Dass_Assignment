from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Car:
    car_id: str
    model: str
    status: str


class InventoryError(ValueError):
    pass


class InventoryModule:
    def __init__(self) -> None:
        self._cars: dict[str, Car] = {}
        self._parts: dict[str, int] = {}
        self._tools: dict[str, int] = {}
        self._cash_balance: float = 0.0

    def add_car(self, car_id: str, model: str) -> Car:
        cleaned_id = car_id.strip() if isinstance(car_id, str) else ""
        cleaned_model = model.strip() if isinstance(model, str) else ""
        if not cleaned_id:
            raise InventoryError("Car ID is required.")
        if not cleaned_model:
            raise InventoryError("Car model is required.")

        key = cleaned_id.casefold()
        if key in self._cars:
            raise InventoryError(f"Car '{cleaned_id}' already exists.")

        car = Car(car_id=cleaned_id, model=cleaned_model, status="ready")
        self._cars[key] = car
        return car

    def get_car(self, car_id: str) -> Car:
        key = self._normalize_key(car_id, "Car ID is required.")
        car = self._cars.get(key)
        if car is None:
            raise InventoryError(f"Car '{car_id.strip()}' does not exist.")
        return car

    def set_car_status(self, car_id: str, status: str) -> Car:
        key = self._normalize_key(car_id, "Car ID is required.")
        cleaned_status = status.strip() if isinstance(status, str) else ""
        if cleaned_status not in {"ready", "damaged", "maintenance"}:
            raise InventoryError("Car status must be one of: ready, damaged, maintenance.")

        existing = self._cars.get(key)
        if existing is None:
            raise InventoryError(f"Car '{car_id.strip()}' does not exist.")

        updated = Car(car_id=existing.car_id, model=existing.model, status=cleaned_status)
        self._cars[key] = updated
        return updated

    def list_cars(self) -> list[Car]:
        return sorted(self._cars.values(), key=lambda car: car.car_id.casefold())

    def add_spare_part(self, part_name: str, quantity: int) -> int:
        return self._add_stock(self._parts, part_name, quantity, "Part name is required.")

    def add_tool(self, tool_name: str, quantity: int) -> int:
        return self._add_stock(self._tools, tool_name, quantity, "Tool name is required.")

    def consume_spare_part(self, part_name: str, quantity: int) -> int:
        return self._consume_stock(self._parts, part_name, quantity, "Part name is required.")

    def consume_tool(self, tool_name: str, quantity: int) -> int:
        return self._consume_stock(self._tools, tool_name, quantity, "Tool name is required.")

    def get_spare_part_quantity(self, part_name: str) -> int:
        key = self._normalize_key(part_name, "Part name is required.")
        return self._parts.get(key, 0)

    def get_tool_quantity(self, tool_name: str) -> int:
        key = self._normalize_key(tool_name, "Tool name is required.")
        return self._tools.get(key, 0)

    def add_cash(self, amount: float) -> float:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InventoryError("Cash amount must be a positive number.")
        self._cash_balance += float(amount)
        return self._cash_balance

    def spend_cash(self, amount: float) -> float:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InventoryError("Cash amount must be a positive number.")
        if amount > self._cash_balance:
            raise InventoryError("Insufficient cash balance.")
        self._cash_balance -= float(amount)
        return self._cash_balance

    def get_cash_balance(self) -> float:
        return self._cash_balance

    def _add_stock(self, stock: dict[str, int], item_name: str, quantity: int, required_msg: str) -> int:
        key = self._normalize_key(item_name, required_msg)
        if not isinstance(quantity, int) or quantity <= 0:
            raise InventoryError("Quantity must be a positive integer.")
        stock[key] = stock.get(key, 0) + quantity
        return stock[key]

    def _consume_stock(self, stock: dict[str, int], item_name: str, quantity: int, required_msg: str) -> int:
        key = self._normalize_key(item_name, required_msg)
        if not isinstance(quantity, int) or quantity <= 0:
            raise InventoryError("Quantity must be a positive integer.")
        current = stock.get(key, 0)
        if quantity > current:
            raise InventoryError("Insufficient quantity in inventory.")
        stock[key] = current - quantity
        return stock[key]

    def _normalize_key(self, value: str, required_msg: str) -> str:
        cleaned = value.strip() if isinstance(value, str) else ""
        if not cleaned:
            raise InventoryError(required_msg)
        return cleaned.casefold()

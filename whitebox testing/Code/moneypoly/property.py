"""Property and PropertyGroup classes for the MoneyPoly board game."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyTerms:
    """Immutable monetary values used by a property."""

    price: int
    base_rent: int


class Property:
    """Represents a single purchasable property tile on the MoneyPoly board."""

    FULL_GROUP_MULTIPLIER = 2

    def __init__(self, name, position, terms, group=None):
        self.name = name
        self.position = position
        self.terms = terms
        self.mortgage_value = terms.price // 2
        self.group = group
        self._state = {"owner": None, "is_mortgaged": False, "houses": 0}
        if group is not None and self not in group.properties:
            group.properties.append(self)

    @property
    def price(self):
        """Return this property's purchase price."""
        return self.terms.price

    @property
    def base_rent(self):
        """Return this property's base rent before modifiers."""
        return self.terms.base_rent

    @property
    def owner(self):
        """Return the current owner, or None when unowned."""
        return self._state["owner"]

    @owner.setter
    def owner(self, value):
        """Set the property's owner."""
        self._state["owner"] = value

    @property
    def is_mortgaged(self):
        """Return True when the property is mortgaged."""
        return self._state["is_mortgaged"]

    @is_mortgaged.setter
    def is_mortgaged(self, value):
        """Set mortgage state for the property."""
        self._state["is_mortgaged"] = value

    @property
    def houses(self):
        """Return the number of houses built on this property."""
        return self._state["houses"]

    @houses.setter
    def houses(self, value):
        """Set the number of houses built on this property."""
        self._state["houses"] = value

    def get_rent(self):
        """Return rent owed for landing on this property."""
        if self.is_mortgaged:
            return 0
        if self.group is not None and self.group.all_owned_by(self.owner):
            return self.base_rent * self.FULL_GROUP_MULTIPLIER
        return self.base_rent

    def mortgage(self):
        """Mortgage this property and return the payout. Returns 0 if already mortgaged."""
        if self.is_mortgaged:
            return 0
        self.is_mortgaged = True
        return self.mortgage_value

    def unmortgage(self):
        """Lift the mortgage. Returns the cost (110% of mortgage value), or 0 if not mortgaged."""
        if not self.is_mortgaged:
            return 0
        cost = int(self.mortgage_value * 1.1)
        self.is_mortgaged = False
        return cost

    def is_available(self):
        """Return True if this property can be purchased."""
        return self.owner is None and not self.is_mortgaged

    def __repr__(self):
        owner_name = self.owner.name if self.owner else "unowned"
        return f"Property({self.name!r}, pos={self.position}, owner={owner_name!r})"


class PropertyGroup:
    """Represents a colour group of properties."""

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.properties = []

    def add_property(self, prop):
        """Add a Property to this group and back-link it."""
        if prop not in self.properties:
            self.properties.append(prop)
            prop.group = self

    def all_owned_by(self, player):
        """Return True if every property in this group is owned by player."""
        if player is None:
            return False
        return all(p.owner == player for p in self.properties)

    def get_owner_counts(self):
        """Return a dict mapping each owner to how many properties they hold in this group."""
        counts = {}
        for prop in self.properties:
            if prop.owner is not None:
                counts[prop.owner] = counts.get(prop.owner, 0) + 1
        return counts

    def size(self):
        """Return the number of properties in this group."""
        return len(self.properties)

    def __repr__(self):
        return f"PropertyGroup({self.name!r}, {len(self.properties)} properties)"

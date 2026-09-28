"""Small deterministic unit conversion table for the MVP bearing scenario."""

from __future__ import annotations

from decimal import Decimal


class IncompatibleUnitError(ValueError):
    """Raised when two units do not share a supported dimension."""


_LINEAR_UNITS: dict[str, tuple[str, Decimal]] = {
    "mm": ("length", Decimal("1")),
    "cm": ("length", Decimal("10")),
    "m": ("length", Decimal("1000")),
    "in": ("length", Decimal("25.4")),
    "n": ("force", Decimal("1")),
    "kn": ("force", Decimal("1000")),
    "rpm": ("speed", Decimal("1")),
}

_TEMPERATURE_UNITS = frozenset({"c", "f", "k"})


def convert_decimal(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """Convert a scalar between supported compatible units."""

    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)
    if source == target:
        return value

    if source in _TEMPERATURE_UNITS and target in _TEMPERATURE_UNITS:
        celsius = _to_celsius(value, source)
        return _from_celsius(celsius, target)

    source_definition = _LINEAR_UNITS.get(source)
    target_definition = _LINEAR_UNITS.get(target)
    if (
        source_definition is None
        or target_definition is None
        or source_definition[0] != target_definition[0]
    ):
        raise IncompatibleUnitError(f"cannot convert {from_unit} to {to_unit}")

    base_value = value * source_definition[1]
    return base_value / target_definition[1]


def normalize_unit(unit: str) -> str:
    normalized = unit.strip().lower().replace("°", "")
    aliases = {
        "millimeter": "mm",
        "millimeters": "mm",
        "centimeter": "cm",
        "centimeters": "cm",
        "meter": "m",
        "meters": "m",
        "inch": "in",
        "inches": "in",
        "newton": "n",
        "newtons": "n",
        "kilonewton": "kn",
        "kilonewtons": "kn",
        "celsius": "c",
        "fahrenheit": "f",
        "kelvin": "k",
    }
    return aliases.get(normalized, normalized)


def _to_celsius(value: Decimal, unit: str) -> Decimal:
    if unit == "c":
        return value
    if unit == "f":
        return (value - Decimal("32")) * Decimal("5") / Decimal("9")
    return value - Decimal("273.15")


def _from_celsius(value: Decimal, unit: str) -> Decimal:
    if unit == "c":
        return value
    if unit == "f":
        return value * Decimal("9") / Decimal("5") + Decimal("32")
    return value + Decimal("273.15")

"""
Calculation services for Infolectric.
Contains power->current conversion, adjusted current and wire recommendation logic.
"""
from decimal import Decimal, InvalidOperation
from typing import List, Dict

from django.db.models import QuerySet

from .models import WireSize


def power_to_current(power_watts: Decimal, voltage: Decimal) -> Decimal:
    """Calculate current I = P / V with validation.

    Raises ValueError on invalid inputs.
    """
    try:
        p = Decimal(power_watts)
        v = Decimal(voltage)
    except (InvalidOperation, TypeError):
        raise ValueError('Invalid numeric values for power or voltage')

    if v == 0:
        raise ValueError('Voltage must be non-zero')

    return p / v


def calculate_current(power_watts: Decimal = None, voltage: Decimal = None, current: Decimal = None) -> Decimal:
    """Compute current using power/voltage or direct current input.

    If both power and voltage are present, use P/V.
    Otherwise, use provided current directly.
    """
    if power_watts is not None:
        if voltage is None:
            voltage = Decimal('220')
        return power_to_current(power_watts, voltage)

    if current is not None:
        try:
            return Decimal(current)
        except (InvalidOperation, TypeError):
            raise ValueError('Invalid current value')

    raise ValueError('Either power/voltage or current must be provided')


SAFETY_FACTOR = Decimal('1.25')


def adjusted_current_for_safety(current: Decimal) -> Decimal:
    """Apply safety factor to current."""
    return Decimal(current) * SAFETY_FACTOR


def recommend_wires_for_current(current: Decimal) -> List[Dict]:
    """
    Return list of wire size dicts that have max_ampacity >= adjusted_current.
    Results ordered by wire_size_mm2 ascending.
    """
    adj = adjusted_current_for_safety(current)
    # Query wire sizes
    qs: QuerySet = WireSize.objects.filter(max_ampacity__gte=adj).order_by('wire_size_mm2')
    results = []
    for w in qs:
        results.append({
            'id': w.id,
            'wire_size_mm2': str(w.wire_size_mm2),
            'max_ampacity': w.max_ampacity,
            'description': w.description,
        })
    return results


def recommend_breaker_for_current(current: Decimal) -> int:
    """
    Simple breaker recommendation: choose the smallest common breaker rating
    that is >= adjusted_current. Returns int (Amps).
    """
    adj = adjusted_current_for_safety(current)
    # Common breaker sizes (Amps)
    common = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200]
    for b in common:
        if Decimal(b) >= adj:
            return b
    return common[-1]

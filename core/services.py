"""
Calculation services for Infolectric.
Contains power->current conversion, adjusted current and wire recommendation logic.
"""
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import List, Dict, Optional

from django.db.models import QuerySet

from .models import ApplianceLoad, WireSize


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


def get_wire_capability(wire_size_id: Optional[int] = None, wire_size: Optional[WireSize] = None) -> Dict:
    """Return wire capability details for explorer mode."""
    if wire_size is None:
        if wire_size_id is None:
            raise ValueError('Wire size id is required')
        wire_size = WireSize.objects.get(pk=wire_size_id)

    max_power = Decimal(wire_size.max_ampacity) * Decimal('220')
    return {
        'id': wire_size.id,
        'wire_size_mm2': str(wire_size.wire_size_mm2),
        'max_ampacity': wire_size.max_ampacity,
        'max_power': max_power,
    }


def get_compatible_appliances(wire_size: WireSize) -> List[Dict]:
    """Return appliances that can safely run on the selected wire size."""
    appliances = ApplianceLoad.objects.filter(
        estimated_current__lte=wire_size.max_ampacity
    ).order_by('estimated_current')

    results = []
    for appliance in appliances:
        results.append({
            'id': appliance.id,
            'name': appliance.name,
            'category': appliance.category.name if appliance.category else None,
            'power_watts': appliance.power_watts,
            'voltage': appliance.voltage,
            'estimated_current': appliance.estimated_current,
        })
    return results


def generate_safe_combinations(wire_size: WireSize, max_combinations: int = 5) -> List[Dict]:
    """Generate safe appliance combinations for the selected wire size."""
    appliances = list(ApplianceLoad.objects.filter(
        estimated_current__lte=wire_size.max_ampacity
    ).order_by('estimated_current'))

    results = []
    max_ampacity = Decimal(wire_size.max_ampacity)

    # Try larger combinations first, then smaller.
    for combination_size in (3, 2, 1):
        if len(results) >= max_combinations:
            break
        for combo in combinations(appliances, combination_size):
            total_current = sum((Decimal(ap.estimated_current or 0) for ap in combo), Decimal('0'))
            if total_current <= max_ampacity:
                utilization = (total_current / max_ampacity) * Decimal('100') if max_ampacity else Decimal('0')
                results.append({
                    'appliances': [appliance.name for appliance in combo],
                    'total_current': total_current.quantize(Decimal('0.01')),
                    'utilization': utilization.quantize(Decimal('0.1')),
                    'wire_limit': max_ampacity,
                    'is_safe': True,
                })
                if len(results) >= max_combinations:
                    break
        if len(results) >= max_combinations:
            break

    results.sort(key=lambda item: item['utilization'], reverse=True)
    return results

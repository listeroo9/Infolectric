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
COPPER_RESISTIVITY = Decimal('0.0000000172')  # Ohm meter for copper
ASSUMED_VOLTAGE = Decimal('220')


def adjusted_current_for_safety(current: Decimal) -> Decimal:
    """Apply safety factor to current."""
    return Decimal(current) * SAFETY_FACTOR


def calculate_wire_resistance(wire_size_mm2: Decimal, length_m: Decimal) -> Decimal:
    """Calculate copper wire resistance for a given cross-sectional area and length."""
    if wire_size_mm2 <= 0 or length_m <= 0:
        raise ValueError('Wire size and length must be positive values')

    area_m2 = wire_size_mm2 * Decimal('0.000001')
    return (COPPER_RESISTIVITY * length_m) / area_m2


def calculate_voltage_drop(current: Decimal, resistance: Decimal) -> Decimal:
    """Compute voltage drop from current and wire resistance."""
    return Decimal(current) * Decimal(resistance)


def calculate_power_loss(current: Decimal, resistance: Decimal) -> Decimal:
    """Compute power loss due to wire resistance."""
    return Decimal(current) * Decimal(current) * Decimal(resistance)


def calculate_voltage_drop_percent(voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute voltage drop percentage."""
    if voltage == 0:
        return Decimal('0')
    return (Decimal(voltage_drop) / Decimal(voltage)) * Decimal('100')


def calculate_efficiency(voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute efficiency as a percentage of delivered voltage."""
    if voltage == 0:
        return Decimal('0')
    return ((Decimal(voltage) - Decimal(voltage_drop)) / Decimal(voltage)) * Decimal('100')


def calculate_load_voltage(source_voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute the voltage available at the appliance after wire losses."""
    return Decimal(source_voltage) - Decimal(voltage_drop)


def get_voltage_drop_warning(voltage_drop_percent: Decimal) -> Dict[str, str]:
    """Return warning status for voltage drop percentages."""
    if voltage_drop_percent < Decimal('3'):
        return {'label': 'Excellent', 'badge': 'success'}
    if voltage_drop_percent <= Decimal('5'):
        return {'label': 'Acceptable', 'badge': 'warning'}
    return {'label': 'Not Recommended', 'badge': 'danger'}


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


def get_wire_capability(wire_size_id: Optional[int] = None, wire_size: Optional[WireSize] = None, wire_length: Decimal = Decimal('10')) -> Dict:
    """Return wire capability details for explorer mode."""
    if wire_size is None:
        if wire_size_id is None:
            raise ValueError('Wire size id is required')
        wire_size = WireSize.objects.get(pk=wire_size_id)

    max_power = Decimal(wire_size.max_ampacity) * ASSUMED_VOLTAGE
    resistance = calculate_wire_resistance(Decimal(wire_size.wire_size_mm2), wire_length)
    voltage_drop = calculate_voltage_drop(Decimal(wire_size.max_ampacity), resistance)
    voltage_drop_percent = calculate_voltage_drop_percent(ASSUMED_VOLTAGE, voltage_drop)
    power_loss = calculate_power_loss(Decimal(wire_size.max_ampacity), resistance)
    efficiency = calculate_efficiency(ASSUMED_VOLTAGE, voltage_drop)
    load_voltage = calculate_load_voltage(ASSUMED_VOLTAGE, voltage_drop)
    warning = get_voltage_drop_warning(voltage_drop_percent)

    return {
        'id': wire_size.id,
        'wire_size_mm2': str(wire_size.wire_size_mm2),
        'max_ampacity': wire_size.max_ampacity,
        'max_power': max_power.quantize(Decimal('0.01')),
        'wire_length': wire_length,
        'resistance': resistance.quantize(Decimal('0.00001')),
        'voltage_drop': voltage_drop.quantize(Decimal('0.01')),
        'voltage_drop_percent': voltage_drop_percent.quantize(Decimal('0.1')),
        'load_voltage': load_voltage.quantize(Decimal('0.01')),
        'power_loss': power_loss.quantize(Decimal('0.01')),
        'efficiency': efficiency.quantize(Decimal('0.1')),
        'warning': warning,
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

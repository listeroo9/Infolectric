"""
Calculation services for Infolectric.
Contains power->current conversion, adjusted current and wire recommendation logic.
"""
from decimal import Decimal, InvalidOperation
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

USAGE_TYPE_SHORT_DURATION = 'short_duration'
USAGE_TYPE_NORMAL_HOUSEHOLD = 'normal_household'
USAGE_TYPE_CONTINUOUS_LOAD = 'continuous_load'

USAGE_TYPE_CHOICES = [
    (USAGE_TYPE_SHORT_DURATION, 'Short Duration'),
    (USAGE_TYPE_NORMAL_HOUSEHOLD, 'Normal Household Use'),
    (USAGE_TYPE_CONTINUOUS_LOAD, 'Continuous Load'),
]

USAGE_TYPE_FACTORS = {
    USAGE_TYPE_SHORT_DURATION: Decimal('1.00'),
    USAGE_TYPE_NORMAL_HOUSEHOLD: Decimal('0.90'),
    USAGE_TYPE_CONTINUOUS_LOAD: Decimal('0.80'),
}

USAGE_TYPE_BADGES = {
    USAGE_TYPE_SHORT_DURATION: 'primary',
    USAGE_TYPE_NORMAL_HOUSEHOLD: 'warning',
    USAGE_TYPE_CONTINUOUS_LOAD: 'danger',
}

USAGE_TYPE_LABELS = {
    USAGE_TYPE_SHORT_DURATION: 'Short Duration',
    USAGE_TYPE_NORMAL_HOUSEHOLD: 'Normal Household Use',
    USAGE_TYPE_CONTINUOUS_LOAD: 'Continuous Load',
}

SAFE_COMBINATION_LEVELS = [
    {
        'level': 1,
        'label': 'Level 1 – Light Load',
        'min': Decimal('0'),
        'max': Decimal('20'),
        'description': 'Very light devices such as chargers and LED lighting. Keep load under 20% of usable capacity.',
    },
    {
        'level': 2,
        'label': 'Level 2 – Moderate Convenience',
        'min': Decimal('20'),
        'max': Decimal('40'),
        'description': 'Everyday household items used for short periods, such as small kitchen gadgets and fans.',
    },
    {
        'level': 3,
        'label': 'Level 3 – Typical Daily Use',
        'min': Decimal('40'),
        'max': Decimal('60'),
        'description': 'Normal household use with a mix of lighting and small appliances over a few hours.',
    },
    {
        'level': 4,
        'label': 'Level 4 – Heavy Household Load',
        'min': Decimal('60'),
        'max': Decimal('80'),
        'description': 'Stronger household equipment used together like space heaters or large kitchen appliances.',
    },
    {
        'level': 5,
        'label': 'Level 5 – Full Capacity',
        'min': Decimal('80'),
        'max': Decimal('100'),
        'description': 'Very high load conditions, close to the wire’s usable limit. Use only when necessary.',
    },
]


def get_safety_factor(usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD) -> Decimal:
    """Return the safety factor for a usage profile."""
    return USAGE_TYPE_FACTORS.get(usage_type, USAGE_TYPE_FACTORS[USAGE_TYPE_NORMAL_HOUSEHOLD])


def get_usage_type_label(usage_type: str) -> str:
    """Return the human readable label for a usage profile."""
    return USAGE_TYPE_LABELS.get(usage_type, USAGE_TYPE_LABELS[USAGE_TYPE_NORMAL_HOUSEHOLD])


def get_usage_type_badge(usage_type: str) -> str:
    """Return the bootstrap badge class for a usage profile."""
    return USAGE_TYPE_BADGES.get(usage_type, USAGE_TYPE_BADGES[USAGE_TYPE_NORMAL_HOUSEHOLD])


def get_utilization_level(utilization: Decimal) -> Dict[str, str]:
    """Return the level metadata for a given utilization percentage."""
    for level in SAFE_COMBINATION_LEVELS:
        if utilization <= level['max']:
            return level
    return SAFE_COMBINATION_LEVELS[-1]


def calculate_usable_current(max_ampacity: Decimal, usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD) -> Decimal:
    """Compute the allowed current for the selected usage type."""
    return Decimal(max_ampacity) * get_safety_factor(usage_type)


def calculate_usable_power(voltage: Decimal, usable_current: Decimal) -> Decimal:
    """Compute usable power from voltage and allowable current."""
    return Decimal(voltage) * Decimal(usable_current)


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


def get_wire_capability(
    wire_size_id: Optional[int] = None,
    wire_size: Optional[WireSize] = None,
    wire_length: Decimal = Decimal('10'),
    usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD
) -> Dict:
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
    safety_factor = get_safety_factor(usage_type)
    usable_current = calculate_usable_current(Decimal(wire_size.max_ampacity), usage_type)
    usable_power = calculate_usable_power(ASSUMED_VOLTAGE, usable_current)

    return {
        'id': wire_size.id,
        'wire_size_mm2': str(wire_size.wire_size_mm2),
        'max_ampacity': wire_size.max_ampacity,
        'max_power_theoretical': max_power.quantize(Decimal('0.01')),
        'recommended_max_power': usable_power.quantize(Decimal('0.01')),
        'wire_length': wire_length,
        'resistance': resistance.quantize(Decimal('0.00001')),
        'voltage_drop': voltage_drop.quantize(Decimal('0.01')),
        'voltage_drop_percent': voltage_drop_percent.quantize(Decimal('0.1')),
        'load_voltage': load_voltage.quantize(Decimal('0.01')),
        'power_loss': power_loss.quantize(Decimal('0.01')),
        'efficiency': efficiency.quantize(Decimal('0.1')),
        'usage_type': usage_type,
        'usage_label': get_usage_type_label(usage_type),
        'usage_badge': get_usage_type_badge(usage_type),
        'safety_factor': safety_factor.quantize(Decimal('0.00')),
        'usable_current': usable_current.quantize(Decimal('0.01')),
        'usable_power': usable_power.quantize(Decimal('0.01')),
        'warning': warning,
    }


def get_compatible_appliances(wire_size: WireSize, usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD) -> List[Dict]:
    """Return appliances that can safely run on the selected wire size."""
    usable_current = calculate_usable_current(Decimal(wire_size.max_ampacity), usage_type)
    appliances = ApplianceLoad.objects.filter(
        estimated_current__lte=usable_current
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


LEVEL_TARGETS = [
    (1, Decimal('0.20')),
    (2, Decimal('0.40')),
    (3, Decimal('0.60')),
    (4, Decimal('0.80')),
    (5, Decimal('0.95')),
]


def generate_safe_combinations(
    wire_size: WireSize,
    usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD,
    max_combinations: int = 5
) -> List[Dict]:
    """Generate safe appliance combinations using deterministic utilization targets."""
    usable_current = calculate_usable_current(Decimal(wire_size.max_ampacity), usage_type)
    appliances = list(ApplianceLoad.objects.filter(
        estimated_current__lte=usable_current
    ).order_by('-estimated_current'))

    if not appliances:
        return []

    max_ampacity = Decimal(wire_size.max_ampacity)
    usable_limit = usable_current
    results = []

    for level, ratio in LEVEL_TARGETS:
        target_current = (usable_limit * ratio).quantize(Decimal('0.01'))
        combo_items = []
        combo_current = Decimal('0')

        for appliance in appliances:
            ap_current = Decimal(appliance.estimated_current or 0)
            if combo_current + ap_current <= target_current:
                combo_items.append(appliance)
                combo_current += ap_current

        if not combo_items:
            fallback = next((ap for ap in reversed(appliances) if Decimal(ap.estimated_current or 0) <= usable_limit), None)
            if fallback:
                combo_items = [fallback]
                combo_current = Decimal(fallback.estimated_current or 0)

        total_power = sum((Decimal(ap.power_watts or 0) for ap in combo_items), Decimal('0'))
        total_voltage = sum((Decimal(ap.voltage or 0) for ap in combo_items), Decimal('0'))
        average_voltage = (total_voltage / len(combo_items)) if combo_items else Decimal('0')
        utilization = (combo_current / usable_limit * Decimal('100')) if usable_limit else Decimal('0')

        appliances_data = []
        for appliance in sorted(combo_items, key=lambda ap: Decimal(ap.estimated_current or 0), reverse=True):
            current = Decimal(appliance.estimated_current or 0)
            contribution_percent = (current / combo_current * Decimal('100')) if combo_current else Decimal('0')
            appliances_data.append({
                'name': appliance.name,
                'power_watts': appliance.power_watts,
                'voltage': appliance.voltage,
                'current_amps': current.quantize(Decimal('0.01')),
                'contribution_percent': contribution_percent.quantize(Decimal('0.1')),
            })

        level_info = next((item for item in SAFE_COMBINATION_LEVELS if item['level'] == level), SAFE_COMBINATION_LEVELS[-1])
        results.append({
            'appliances': appliances_data,
            'device_count': len(combo_items),
            'total_current': combo_current.quantize(Decimal('0.01')),
            'total_power': total_power.quantize(Decimal('0.01')),
            'average_voltage': average_voltage.quantize(Decimal('0.1')),
            'utilization': utilization.quantize(Decimal('0.1')),
            'wire_limit': max_ampacity,
            'usable_limit': usable_limit.quantize(Decimal('0.01')),
            'level': level,
            'level_label': level_info['label'],
            'level_description': level_info['description'],
            'is_safe': True,
        })

    return results[:max_combinations]


def util_better(candidate: Dict, current: Dict) -> bool:
    """Choose the better combination for a given utilization level."""
    if candidate['utilization'] != current['utilization']:
        return candidate['utilization'] > current['utilization']
    if candidate['device_count'] != current['device_count']:
        return candidate['device_count'] > current['device_count']
    return candidate['total_current'] > current['total_current']

"""
Calculation services for Infolectric.
Contains power->current conversion, adjusted current and wire recommendation logic.
"""
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional

from django.db.models import QuerySet

from .models import ApplianceLoad, WireSize


def to_decimal(value) -> Decimal:
    """Normalize numeric input to Decimal using string conversion."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('Invalid numeric value')


def assert_decimal(value, name: str = 'value') -> Decimal:
    """Assert that the provided value is a Decimal."""
    if not isinstance(value, Decimal):
        raise TypeError(f'{name} must be Decimal, got {type(value).__name__}')
    return value


def format_decimal(value, places: int) -> Decimal:
    """Quantize a Decimal to the given number of decimal places and return a Decimal.

    Keeps internal precision but provides a human-friendly rounded value for output.
    """
    d = to_decimal(value)
    assert_decimal(d)
    if places < 0:
        raise ValueError('places must be non-negative')
    quant = Decimal('1').scaleb(-places)
    return d.quantize(quant)


def power_to_current(power_watts: Decimal, voltage: Decimal) -> Decimal:
    """Calculate current I = P / V with validation.

    Raises ValueError on invalid inputs.
    """
    p = to_decimal(power_watts)
    v = to_decimal(voltage)
    assert_decimal(p, 'power_watts')
    assert_decimal(v, 'voltage')

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
        return to_decimal(current)

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
    current = to_decimal(max_ampacity)
    assert_decimal(current, 'max_ampacity')
    return current * get_safety_factor(usage_type)


def calculate_usable_power(voltage: Decimal, usable_current: Decimal) -> Decimal:
    """Compute usable power from voltage and allowable current."""
    voltage_value = to_decimal(voltage)
    current_value = to_decimal(usable_current)
    assert_decimal(voltage_value, 'voltage')
    assert_decimal(current_value, 'usable_current')
    return voltage_value * current_value


def adjusted_current_for_safety(current: Decimal) -> Decimal:
    """Apply safety factor to current."""
    current_value = to_decimal(current)
    assert_decimal(current_value, 'current')
    return current_value * SAFETY_FACTOR


def calculate_wire_resistance(wire_size_mm2: Decimal, length_m: Decimal) -> Decimal:
    """Calculate copper wire resistance for a given cross-sectional area and length."""
    wire_size_mm2 = to_decimal(wire_size_mm2)
    length_m = to_decimal(length_m)
    assert_decimal(wire_size_mm2, 'wire_size_mm2')
    assert_decimal(length_m, 'length_m')

    if wire_size_mm2 <= 0 or length_m <= 0:
        raise ValueError('Wire size and length must be positive values')

    area_m2 = wire_size_mm2 * Decimal('0.000001')
    return (COPPER_RESISTIVITY * length_m) / area_m2


def calculate_voltage_drop(current: Decimal, resistance: Decimal) -> Decimal:
    """Compute voltage drop from current and wire resistance."""
    current_value = to_decimal(current)
    resistance_value = to_decimal(resistance)
    assert_decimal(current_value, 'current')
    assert_decimal(resistance_value, 'resistance')
    return current_value * resistance_value


def calculate_power_loss(current: Decimal, resistance: Decimal) -> Decimal:
    """Compute power loss due to wire resistance."""
    current_value = to_decimal(current)
    resistance_value = to_decimal(resistance)
    assert_decimal(current_value, 'current')
    assert_decimal(resistance_value, 'resistance')
    return current_value * current_value * resistance_value


def calculate_voltage_drop_percent(voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute voltage drop percentage."""
    voltage_value = to_decimal(voltage)
    voltage_drop_value = to_decimal(voltage_drop)
    assert_decimal(voltage_value, 'voltage')
    assert_decimal(voltage_drop_value, 'voltage_drop')
    if voltage_value == 0:
        return Decimal('0')
    return (voltage_drop_value / voltage_value) * Decimal('100')


def calculate_efficiency(voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute efficiency as a percentage of delivered voltage."""
    voltage_value = to_decimal(voltage)
    voltage_drop_value = to_decimal(voltage_drop)
    assert_decimal(voltage_value, 'voltage')
    assert_decimal(voltage_drop_value, 'voltage_drop')
    if voltage_value == 0:
        return Decimal('0')
    return ((voltage_value - voltage_drop_value) / voltage_value) * Decimal('100')


def calculate_load_voltage(source_voltage: Decimal, voltage_drop: Decimal) -> Decimal:
    """Compute the voltage available at the appliance after wire losses."""
    source_voltage_value = to_decimal(source_voltage)
    voltage_drop_value = to_decimal(voltage_drop)
    assert_decimal(source_voltage_value, 'source_voltage')
    assert_decimal(voltage_drop_value, 'voltage_drop')
    return source_voltage_value - voltage_drop_value


def get_voltage_drop_warning(voltage_drop_percent: Decimal) -> Dict[str, str]:
    """Return warning status for voltage drop percentages."""
    voltage_drop_percent = to_decimal(voltage_drop_percent)
    assert_decimal(voltage_drop_percent, 'voltage_drop_percent')
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
        # Build a presentation-friendly capability snapshot for each wire
        cap = get_wire_capability(wire_size=w)
        results.append({
            'id': w.id,
            'wire_size_mm2': str(w.wire_size_mm2),
            # max_ampacity formatted to 2 decimals
            'max_ampacity': cap['max_ampacity'],
            'description': w.description,
            # include key capability values to avoid recomputing in the UI
            'resistance': cap['resistance'],
            'voltage_drop': cap['voltage_drop'],
            'voltage_drop_percent': cap['voltage_drop_percent'],
            'efficiency': cap['efficiency'],
            'max_power_theoretical': cap['max_power_theoretical'],
            'recommended_max_power': cap['recommended_max_power'],
            'usable_current': cap['usable_current'],
            'usable_power': cap['usable_power'],
            'wire_length': cap['wire_length'],
            'warning': cap['warning'],
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

    wire_length = to_decimal(wire_length)
    assert_decimal(wire_length, 'wire_length')
    max_ampacity = to_decimal(wire_size.max_ampacity)
    assert_decimal(max_ampacity, 'wire_size.max_ampacity')

    max_power = max_ampacity * ASSUMED_VOLTAGE
    resistance = calculate_wire_resistance(to_decimal(wire_size.wire_size_mm2), wire_length)
    voltage_drop = calculate_voltage_drop(max_ampacity, resistance)
    voltage_drop_percent = calculate_voltage_drop_percent(ASSUMED_VOLTAGE, voltage_drop)
    power_loss = calculate_power_loss(to_decimal(wire_size.max_ampacity), resistance)
    efficiency = calculate_efficiency(ASSUMED_VOLTAGE, voltage_drop)
    load_voltage = calculate_load_voltage(ASSUMED_VOLTAGE, voltage_drop)
    warning = get_voltage_drop_warning(voltage_drop_percent)
    safety_factor = get_safety_factor(usage_type)
    usable_current = calculate_usable_current(to_decimal(wire_size.max_ampacity), usage_type)
    usable_power = calculate_usable_power(ASSUMED_VOLTAGE, usable_current)

    # Apply output formatting rules (quantize at output boundary):
    # max_ampacity -> 2 decimals
    # Voltage values -> 2 decimals
    # Current values -> 3 decimals
    # Resistance -> 5 decimals
    # Power values -> 2 decimals
    # Percent values -> 2 decimals
    # Efficiency -> 2 decimals
    return {
        'id': wire_size.id,
        'wire_size_mm2': str(wire_size.wire_size_mm2),
        'max_ampacity': format_decimal(max_ampacity, 2),
        'max_power_theoretical': format_decimal(max_power, 2),
        'recommended_max_power': format_decimal(usable_power, 2),
        'wire_length': format_decimal(wire_length, 3),
        'resistance': format_decimal(resistance, 5),
        'voltage_drop': format_decimal(voltage_drop, 3),
        'voltage_drop_percent': format_decimal(voltage_drop_percent, 2),
        'load_voltage': format_decimal(load_voltage, 2),
        'power_loss': format_decimal(power_loss, 2),
        'efficiency': format_decimal(efficiency, 2),
        'usage_type': usage_type,
        'usage_label': get_usage_type_label(usage_type),
        'usage_badge': get_usage_type_badge(usage_type),
        'safety_factor': format_decimal(safety_factor, 2),
        'usable_current': format_decimal(usable_current, 3),
        'usable_power': format_decimal(usable_power, 2),
        'warning': warning,
    }


def get_compatible_appliances(wire_size: WireSize, usage_type: str = USAGE_TYPE_NORMAL_HOUSEHOLD) -> List[Dict]:
    """Return appliances that can safely run on the selected wire size."""
    usable_current = calculate_usable_current(to_decimal(wire_size.max_ampacity), usage_type)
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
    usable_current = calculate_usable_current(to_decimal(wire_size.max_ampacity), usage_type)
    appliances = list(ApplianceLoad.objects.filter(
        estimated_current__lte=usable_current
    ).order_by('-estimated_current'))

    if not appliances:
        return []

    max_ampacity = to_decimal(wire_size.max_ampacity)
    usable_limit = usable_current
    results = []

    for level, ratio in LEVEL_TARGETS:
        target_current = (usable_limit * ratio).quantize(Decimal('0.01'))
        combo_items = []
        combo_current = Decimal('0')

        for appliance in appliances:
            ap_current = to_decimal(appliance.estimated_current or 0)
            if combo_current + ap_current <= target_current:
                combo_items.append(appliance)
                combo_current += ap_current

        if not combo_items:
            fallback = next((ap for ap in reversed(appliances) if to_decimal(ap.estimated_current or 0) <= usable_limit), None)
            if fallback:
                combo_items = [fallback]
                combo_current = to_decimal(fallback.estimated_current or 0)

        total_power = sum((to_decimal(ap.power_watts or 0) for ap in combo_items), Decimal('0'))
        total_voltage = sum((to_decimal(ap.voltage or 0) for ap in combo_items), Decimal('0'))
        average_voltage = (total_voltage / len(combo_items)) if combo_items else Decimal('0')
        utilization = (combo_current / usable_limit * Decimal('100')) if usable_limit else Decimal('0')

        appliances_data = []
        for appliance in sorted(combo_items, key=lambda ap: to_decimal(ap.estimated_current or 0), reverse=True):
            current = to_decimal(appliance.estimated_current or 0)
            contribution_percent = (current / combo_current * Decimal('100')) if combo_current else Decimal('0')
            appliances_data.append({
                'name': appliance.name,
                'power_watts': format_decimal(appliance.power_watts, 2),
                'voltage': format_decimal(appliance.voltage, 3),
                'current_amps': format_decimal(current, 3),
                'contribution_percent': format_decimal(contribution_percent, 2),
            })

        level_info = next((item for item in SAFE_COMBINATION_LEVELS if item['level'] == level), SAFE_COMBINATION_LEVELS[-1])
        results.append({
            'appliances': appliances_data,
            'device_count': len(combo_items),
            'total_current': format_decimal(combo_current, 3),
            'total_power': format_decimal(total_power, 2),
            'average_voltage': format_decimal(average_voltage, 3),
            'utilization': format_decimal(utilization, 2),
            'wire_limit': format_decimal(max_ampacity, 3),
            'usable_limit': format_decimal(usable_limit, 3),
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

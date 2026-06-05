from decimal import Decimal, getcontext
import traceback
import os
import sys

# ensure project root is on sys.path so `core` app is importable
script_dir = os.path.dirname(__file__)
# project root (app root) is one level up from this scripts directory
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# increase precision for tests
getcontext().prec = 28

try:
    # configure Django settings so model imports work during standalone run
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infolectric.settings')
    import django
    django.setup()

    from core import services as s
except Exception as e:
    print('IMPORT ERROR in core.services:', e)
    traceback.print_exc()
    raise

class WireLike:
    def __init__(self):
        self.id = 1
        self.wire_size_mm2 = Decimal('2.5')
        self.max_ampacity = Decimal('16')
        self.description = 'test wire'

class ApplianceLike:
    def __init__(self, power, voltage):
        self.power_watts = power
        self.voltage = voltage


def run_checks():
    errors = []
    try:
        print('power_to_current:', s.power_to_current(Decimal('1500'), Decimal('230')))
    except Exception as e:
        print('ERR power_to_current', e)
        traceback.print_exc()
        errors.append(('power_to_current', e))

    try:
        print('calculate_current:', s.calculate_current(Decimal('1500'), Decimal('230')))
    except Exception as e:
        print('ERR calculate_current', e)
        traceback.print_exc()
        errors.append(('calculate_current', e))

    try:
        w = WireLike()
        cap = s.get_wire_capability(wire_size=w, wire_length=Decimal('10'), usage_type=s.USAGE_TYPE_NORMAL_HOUSEHOLD)
        print('get_wire_capability keys:', list(cap.keys()))
    except Exception as e:
        print('ERR get_wire_capability', e)
        traceback.print_exc()
        errors.append(('get_wire_capability', e))

    try:
        combos = s.generate_safe_combinations(wire_size=w, usage_type=s.USAGE_TYPE_NORMAL_HOUSEHOLD)
        print('generate_safe_combinations len:', len(combos))
        if combos:
            print('sample combo keys:', combos[0].keys())
    except Exception as e:
        print('ERR generate_safe_combinations', e)
        traceback.print_exc()
        errors.append(('generate_safe_combinations', e))

    try:
        ap = ApplianceLike(Decimal('500'), Decimal('230'))
        contrib = s.calculate_usages = None
        # call a few more functions if present
        if hasattr(s, 'calculate_voltage_drop'):
            print('calculate_voltage_drop:', s.calculate_voltage_drop(Decimal('2.5'), Decimal('10'), Decimal('10'), Decimal('230')))
    except Exception as e:
        print('ERR additional checks', e)
        traceback.print_exc()
        errors.append(('additional', e))

    if errors:
        print('\nSummary of errors:')
        for name, err in errors:
            print('-', name, type(err), err)
    else:
        print('\nAll sanity checks passed')

if __name__ == '__main__':
    run_checks()

"""
Management command to seed realistic ApplianceLoad entries.

Usage:
  python manage.py seed_appliances [--count N] [--reset] [--seed S]

Options:
  --count N   Number of appliance records to create (default 75, min 50)
  --reset     Delete existing ApplianceLoad entries before seeding
  --seed S    Optional random seed for reproducible output
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
import random

from core.models import ApplianceLoad, Category


APPLIANCE_DEFINITIONS = [
    # Household Appliances
    ("Rice Cooker", "Household Appliances", 500, 1000, 220),
    ("Electric Fan", "Household Appliances", 40, 80, 220),
    ("Refrigerator", "Household Appliances", 100, 400, 220),
    ("Air Conditioner", "Household Appliances", 1000, 3000, 220),
    ("Microwave Oven", "Household Appliances", 600, 1200, 220),
    ("Electric Kettle", "Household Appliances", 1500, 3000, 220),
    ("Washing Machine", "Household Appliances", 300, 1200, 220),

    # Electronics
    ("Laptop Charger", "Electronics", 45, 120, 220),
    ("Desktop PC", "Electronics", 200, 800, 220),
    ("Monitor", "Electronics", 20, 150, 220),
    ("Printer", "Electronics", 30, 300, 220),
    ("Router", "Electronics", 5, 30, 220),

    # Kitchen Appliances
    ("Blender", "Kitchen Appliances", 200, 800, 220),
    ("Toaster", "Kitchen Appliances", 800, 1600, 220),
    ("Oven", "Kitchen Appliances", 1000, 3000, 220),
    ("Coffee Maker", "Kitchen Appliances", 600, 1500, 220),

    # Tools / Others
    ("Drill", "Tools", 300, 1200, 220),
    ("Soldering Iron", "Tools", 20, 80, 220),
    ("Water Pump", "Tools", 200, 2000, 220),
]

VARIANTS = [
    "Small",
    "Medium",
    "Large",
    "Industrial",
    "Portable",
    "Heavy Duty",
    "Compact",
]


class Command(BaseCommand):
    help = 'Seed ApplianceLoad entries with realistic sample data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=75, help='Number of appliance records to create (min 50)')
        parser.add_argument('--reset', action='store_true', help='Delete existing ApplianceLoad entries before seeding')
        parser.add_argument('--seed', type=int, help='Random seed for reproducible outputs')

    def handle(self, *args, **options):
        count = options.get('count') or 75
        if count < 50:
            self.stdout.write(self.style.WARNING('Count less than 50 — using minimum 50'))
            count = 50

        if options.get('seed') is not None:
            random.seed(int(options.get('seed')))

        if options.get('reset'):
            deleted, _ = ApplianceLoad.objects.all().delete()
            self.stdout.write(self.style.NOTICE(f'Deleted {deleted} existing ApplianceLoad objects'))

        # Ensure categories exist
        category_map = {}
        for _, cat_name, *_ in APPLIANCE_DEFINITIONS:
            cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'description': f'{cat_name} sample category'})
            category_map[cat_name] = cat

        created = 0
        skipped = 0

        # Build a large pool of candidate appliances by combining definitions with variants
        candidates = []
        for base_name, cat_name, pmin, pmax, voltage in APPLIANCE_DEFINITIONS:
            # always include the base variant
            candidates.append((base_name, cat_name, pmin, pmax, voltage))
            # add named variants
            for v in VARIANTS:
                candidates.append((f"{base_name} - {v}", cat_name, pmin, pmax, voltage))
            # add numbered variants to increase pool
            for i in range(1, 6):
                candidates.append((f"{base_name} #{i}", cat_name, pmin, pmax, voltage))

        # Shuffle candidates and iterate until we have desired count or exhaust
        random.shuffle(candidates)

        idx = 0
        attempts = 0
        max_attempts = len(candidates) * 3

        while created < count and attempts < max_attempts and idx < len(candidates):
            name, cat_name, pmin, pmax, voltage = candidates[idx]
            idx += 1
            attempts += 1

            # randomize power in realistic range
            power = round(random.uniform(pmin, pmax), 2)

            # Ensure uniqueness: try to get_or_create by exact name
            defaults = {
                'voltage': Decimal(str(voltage)),
                'power_watts': Decimal(str(power)),
                'category': category_map.get(cat_name)
            }
            obj, created_flag = ApplianceLoad.objects.get_or_create(name=name, defaults=defaults)
            if created_flag:
                created += 1
                # saved via model.save() so estimated_current auto-calculated
                self.stdout.write(self.style.SUCCESS(f'Created: {obj.name} ({power}W @ {voltage}V)'))
            else:
                # if exists but fields differ, offer an option to update or skip; we skip to avoid overwriting
                skipped += 1

            # If we reach end of list but still need more, expand candidates by adding numbered suffixes
            if idx >= len(candidates) and created < count:
                # generate more numbered variants
                base_pool = [c for c in APPLIANCE_DEFINITIONS]
                for base_name, cat_name, pmin, pmax, voltage in base_pool:
                    for i in range(100, 200):
                        candidates.append((f"{base_name} - X{i}", cat_name, pmin, pmax, voltage))
                random.shuffle(candidates)

        self.stdout.write(self.style.SUCCESS(f'✓ Appliances created: {created}'))
        if skipped:
            self.stdout.write(self.style.NOTICE(f'Appliances skipped (already existed): {skipped}'))
        if created < count:
            self.stdout.write(self.style.WARNING(f'Requested {count} created but only {created} were added (pool exhausted)'))
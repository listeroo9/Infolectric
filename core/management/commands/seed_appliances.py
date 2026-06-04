"""
Management command to seed realistic ApplianceLoad entries deterministically.

Usage:
  python manage.py seed_appliances [--reset]

Notes:
- This command uses a structured appliance catalog with fixed wattage tiers.
- No random power generation or numeric suffixes are used.
- Safe to re-run; uses get_or_create().
"""
from django.core.management.base import BaseCommand
from decimal import Decimal

from core.models import ApplianceLoad, Category


# Structured appliance catalog: category -> base entries with labeled variants
APPLIANCE_CATALOG = [
    # Household Appliances
    {
        'category': 'Household Appliances',
        'base_name': 'Electric Fan',
        'variants': [
            ('Small', 40),
            ('Medium', 60),
            ('Industrial', 120),
        ],
        'voltage': 220,
    },
    {
        'category': 'Household Appliances',
        'base_name': 'Air Conditioner',
        'variants': [
            ('Window Type', 1000),
            ('Split (Small)', 1500),
            ('Split (Large)', 2500),
            ('Large Unit', 3000),
        ],
        'voltage': 220,
    },
    {
        'category': 'Household Appliances',
        'base_name': 'Rice Cooker',
        'variants': [
            ('Small', 500),
            ('Medium', 700),
            ('Large', 900),
        ],
        'voltage': 220,
    },
    {
        'category': 'Household Appliances',
        'base_name': 'Refrigerator',
        'variants': [
            ('Mini', 100),
            ('Standard', 150),
            ('Large', 250),
        ],
        'voltage': 220,
    },
    {
        'category': 'Household Appliances',
        'base_name': 'Washing Machine',
        'variants': [
            ('Standard', 500),
            ('Heavy Duty', 1000),
        ],
        'voltage': 220,
    },

    # Kitchen Appliances
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Blender',
        'variants': [
            ('Small', 300),
            ('Standard', 500),
            ('Industrial', 800),
        ],
        'voltage': 220,
    },
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Microwave Oven',
        'variants': [
            ('Standard', 800),
            ('Standard Plus', 1000),
            ('High Power', 1200),
        ],
        'voltage': 220,
    },
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Electric Kettle',
        'variants': [
            ('Standard', 1500),
            ('Medium', 1800),
            ('High Power', 2200),
        ],
        'voltage': 220,
    },
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Toaster',
        'variants': [
            ('2-Slice', 800),
            ('4-Slice', 1200),
        ],
        'voltage': 220,
    },
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Coffee Maker',
        'variants': [
            ('Standard', 600),
            ('Espresso', 1200),
        ],
        'voltage': 220,
    },
    {
        'category': 'Kitchen Appliances',
        'base_name': 'Oven',
        'variants': [
            ('Small', 1000),
            ('Standard', 2000),
            ('Large', 3000),
        ],
        'voltage': 220,
    },

    # Electronics
    {
        'category': 'Electronics',
        'base_name': 'Laptop Charger',
        'variants': [
            ('45W', 45),
            ('65W', 65),
            ('90W', 90),
            ('120W', 120),
        ],
        'voltage': 220,
    },
    {
        'category': 'Electronics',
        'base_name': 'Desktop PC',
        'variants': [
            ('Low-end', 300),
            ('Mid-range', 450),
            ('High-end', 600),
        ],
        'voltage': 220,
    },
    {
        'category': 'Electronics',
        'base_name': 'Monitor',
        'variants': [
            ('Small', 20),
            ('Standard', 40),
            ('Large', 75),
            ('High Power', 100),
        ],
        'voltage': 220,
    },
    {
        'category': 'Electronics',
        'base_name': 'Printer',
        'variants': [
            ('Inkjet', 50),
            ('Laser', 300),
        ],
        'voltage': 220,
    },
    {
        'category': 'Electronics',
        'base_name': 'Router',
        'variants': [
            ('Small', 5),
            ('Standard', 12),
            ('High Performance', 20),
        ],
        'voltage': 220,
    },

    # Tools / Others
    {
        'category': 'Tools',
        'base_name': 'Drill',
        'variants': [
            ('Light Duty', 500),
            ('Standard', 750),
            ('Heavy Duty', 1000),
        ],
        'voltage': 220,
    },
    {
        'category': 'Tools',
        'base_name': 'Soldering Iron',
        'variants': [
            ('Low Power', 30),
            ('Standard', 50),
            ('High Power', 80),
        ],
        'voltage': 220,
    },
    {
        'category': 'Tools',
        'base_name': 'Water Pump',
        'variants': [
            ('Small', 500),
            ('Standard', 1000),
            ('Large', 1500),
        ],
        'voltage': 220,
    },
]


class Command(BaseCommand):
    help = 'Seed ApplianceLoad entries with a structured, realistic dataset.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing ApplianceLoad entries before seeding')

    def handle(self, *args, **options):
        if options.get('reset'):
            deleted, _ = ApplianceLoad.objects.all().delete()
            self.stdout.write(self.style.NOTICE(f'Deleted {deleted} existing ApplianceLoad objects'))

        created = 0
        skipped = 0
        breakdown_by_category = {}
        variants_count = {}

        # Ensure categories exist
        category_map = {}
        for entry in APPLIANCE_CATALOG:
            cat_name = entry['category']
            cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'description': f'{cat_name} sample category'})
            category_map[cat_name] = cat

        for entry in APPLIANCE_CATALOG:
            base_name = entry['base_name']
            cat_name = entry['category']
            voltage = entry.get('voltage', 220)
            variants = entry['variants']
            variants_count[base_name] = len(variants)

            for variant_label, power in variants:
                # deterministic display name
                name = f"{base_name} ({variant_label})"
                defaults = {
                    'voltage': Decimal(str(voltage)),
                    'power_watts': Decimal(str(power)),
                    'category': category_map.get(cat_name),
                }
                obj, created_flag = ApplianceLoad.objects.get_or_create(name=name, defaults=defaults)
                if created_flag:
                    created += 1
                    breakdown_by_category.setdefault(cat_name, 0)
                    breakdown_by_category[cat_name] += 1
                    self.stdout.write(self.style.SUCCESS(f'Created: {name} — {power}W @ {voltage}V'))
                else:
                    skipped += 1

        # Summary output
        self.stdout.write(self.style.SUCCESS(f'\nSeeding completed.'))
        self.stdout.write(self.style.SUCCESS(f'Appliances created: {created}'))
        self.stdout.write(self.style.NOTICE(f'Appliances skipped (already existed): {skipped}'))
        self.stdout.write(self.style.SUCCESS('\nBreakdown by category:'))
        for cat, cnt in breakdown_by_category.items():
            self.stdout.write(self.style.SUCCESS(f'  - {cat}: {cnt}'))

        self.stdout.write(self.style.SUCCESS('\nVariants per appliance type:'))
        for base, cnt in variants_count.items():
            self.stdout.write(self.style.SUCCESS(f'  - {base}: {cnt}'))
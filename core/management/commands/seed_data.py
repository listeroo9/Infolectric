"""
Django management command to seed the database with sample data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from core.models import Category, Component, WireSize


class Command(BaseCommand):
    """Command to populate the database with sample electrical data."""
    help = 'Seed the database with sample electrical components and wire sizes'

    def handle(self, *args, **options):
        # ====================================================================
        # CREATE CATEGORIES
        # ====================================================================
        categories_data = [
            {
                'name': 'Resistors',
                'description': 'Passive components that resist electric current flow'
            },
            {
                'name': 'Capacitors',
                'description': 'Components that store electrical energy in an electric field'
            },
            {
                'name': 'Inductors',
                'description': 'Components that store electrical energy in a magnetic field'
            },
            {
                'name': 'Diodes',
                'description': 'Semiconductor devices that conduct electricity in one direction'
            },
            {
                'name': 'Transistors',
                'description': 'Semiconductor devices used for amplification and switching'
            },
            {
                'name': 'Transformers',
                'description': 'Electrical devices that transfer energy between circuits'
            },
            {
                'name': 'Relays',
                'description': 'Electromechanical switches controlled by electrical signals'
            },
            {
                'name': 'Switches',
                'description': 'Devices for making and breaking electrical circuits'
            },
            {
                'name': 'Circuit Breakers',
                'description': 'Automatic switches that protect circuits from overcurrent'
            },
            {
                'name': 'Fuses',
                'description': 'Protective devices that break circuits when current exceeds safe levels'
            }
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = cat
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'{status}: {cat.name}')

        # ====================================================================
        # CREATE COMPONENTS
        # ====================================================================
        components_data = [
            {
                'name': 'Carbon Film Resistor 10kΩ',
                'description': 'Standard carbon film resistor with 10 kilohm resistance. Common value for general purpose use. 1/4W power rating.',
                'category': 'Resistors'
            },
            {
                'name': 'Electrolytic Capacitor 100μF',
                'description': 'Large capacitor commonly used for power supply filtering and energy storage. 50V rated voltage.',
                'category': 'Capacitors'
            },
            {
                'name': 'Air Core Inductor 10μH',
                'description': 'Small inductance coil for RF circuits and filter applications. Air core design for low losses.',
                'category': 'Inductors'
            },
            {
                'name': '1N4148 Signal Diode',
                'description': 'Fast switching diode used in signal processing circuits. High frequency capable.',
                'category': 'Diodes'
            },
            {
                'name': '2N2222 NPN Transistor',
                'description': 'General purpose NPN bipolar junction transistor. Classic component for amplification and switching applications.',
                'category': 'Transistors'
            },
            {
                'name': 'Step-Down Transformer 230V/12V',
                'description': 'Power transformer converting 230V AC to 12V AC output. 500VA rated power. Common for power supplies.',
                'category': 'Transformers'
            },
            {
                'name': 'Automotive Relay 12V/20A',
                'description': 'Four-pole relay for switching high-current circuits in vehicles. 12V DC coil voltage.',
                'category': 'Relays'
            },
            {
                'name': 'Toggle Switch SPDT',
                'description': 'Single Pole Double Throw momentary switch. Common for manual circuit control. 10A rated current.',
                'category': 'Switches'
            },
            {
                'name': 'Mini Circuit Breaker 16A/230V',
                'description': 'Single pole circuit breaker for household use. Protects circuits up to 16 amps. Type C curve.',
                'category': 'Circuit Breakers'
            },
            {
                'name': 'Ceramic Fuse 10A/250V',
                'description': 'Fast-blow ceramic fuse for general circuit protection. 10 amp rating at 250V AC.',
                'category': 'Fuses'
            }
        ]

        for comp_data in components_data:
            comp, created = Component.objects.get_or_create(
                name=comp_data['name'],
                defaults={
                    'description': comp_data['description'],
                    'category': categories[comp_data['category']]
                }
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'{status}: {comp.name}')

        # ====================================================================
        # CREATE WIRE SIZES
        # ====================================================================
        wire_sizes_data = [
            {'wire_size_mm2': 0.75, 'max_ampacity': 6, 'description': 'Very small gauge, signal and low-power applications'},
            {'wire_size_mm2': 1.0, 'max_ampacity': 10, 'description': 'Small gauge for light fixtures and doorbell circuits'},
            {'wire_size_mm2': 1.5, 'max_ampacity': 15, 'description': 'Common for lighting circuits in residential wiring'},
            {'wire_size_mm2': 2.5, 'max_ampacity': 20, 'description': 'Standard for household outlet circuits'},
            {'wire_size_mm2': 4, 'max_ampacity': 32, 'description': 'Heavy duty residential circuits, kitchen appliances'},
            {'wire_size_mm2': 6, 'max_ampacity': 46, 'description': 'Main circuit feeds, high-power appliances'},
            {'wire_size_mm2': 10, 'max_ampacity': 66, 'description': 'Industrial and large building mains'},
            {'wire_size_mm2': 16, 'max_ampacity': 91, 'description': 'Heavy industrial power distribution'},
            {'wire_size_mm2': 25, 'max_ampacity': 125, 'description': 'Large cable for main distribution boards'},
            {'wire_size_mm2': 35, 'max_ampacity': 160, 'description': 'Extra heavy duty industrial applications'},
            {'wire_size_mm2': 50, 'max_ampacity': 200, 'description': 'Three-phase industrial power mains'},
            {'wire_size_mm2': 70, 'max_ampacity': 270, 'description': 'Large scale industrial distribution'},
            {'wire_size_mm2': 95, 'max_ampacity': 350, 'description': 'Heavy gauge for power stations and large installations'},
            {'wire_size_mm2': 120, 'max_ampacity': 410, 'description': 'Maximum standard size for most installations'},
        ]

        for wire_data in wire_sizes_data:
            wire, created = WireSize.objects.get_or_create(
                wire_size_mm2=wire_data['wire_size_mm2'],
                defaults={
                    'max_ampacity': wire_data['max_ampacity'],
                    'description': wire_data['description']
                }
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'{status}: {wire.wire_size_mm2}mm² ({wire.max_ampacity}A)')

        self.stdout.write(self.style.SUCCESS('✓ Database seeding completed successfully!'))

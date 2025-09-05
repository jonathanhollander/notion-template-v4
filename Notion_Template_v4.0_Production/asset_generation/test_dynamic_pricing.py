#!/usr/bin/env python3
"""Test dynamic pricing implementation"""

from asset_generator import AssetGenerator

# Initialize generator
generator = AssetGenerator()

# Test model price lookups
models_to_test = [
    ('stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc', 'SDXL'),
    ('black-forest-labs/flux-1.1-pro:80a09d66baa990429c2f5ae8a4306bf778a1b3775afd01cc2cc8bdbe9033769c', 'Flux Pro'),
    ('unknown-model/test', 'Unknown Model')
]

print("DYNAMIC PRICING TEST")
print("=" * 50)
print()

for model_id, name in models_to_test:
    price = generator.get_model_price(model_id)
    print(f"{name}:")
    print(f"  Model ID: {model_id[:30]}...")
    print(f"  Price: ${price:.3f}")
    print()

# Calculate costs for 15-item test
print("\n15-ITEM TEST GENERATION COSTS:")
print("-" * 30)
icons_cost = 7 * generator.get_model_price('stability-ai/sdxl')
covers_cost = 5 * generator.get_model_price('black-forest-labs/flux-1.1-pro')
letter_cost = 1 * generator.get_model_price('black-forest-labs/flux-1.1-pro')
db_icon_cost = 1 * generator.get_model_price('stability-ai/sdxl')
texture_cost = 1 * generator.get_model_price('stability-ai/sdxl')

print(f"7 Icons (SDXL):           ${icons_cost:.3f}")
print(f"5 Covers (Flux Pro):      ${covers_cost:.3f}")
print(f"1 Letter Header (Flux):   ${letter_cost:.3f}")
print(f"1 Database Icon (SDXL):   ${db_icon_cost:.3f}")
print(f"1 Texture (SDXL):         ${texture_cost:.3f}")
print("-" * 30)
total_cost = icons_cost + covers_cost + letter_cost + db_icon_cost + texture_cost
print(f"TOTAL:                    ${total_cost:.3f}")

# Compare with old hardcoded pricing
old_cost = 15 * 0.04
print(f"\nOld hardcoded cost (15 × $0.04): ${old_cost:.2f}")
print(f"New dynamic cost:                 ${total_cost:.3f}")
print(f"Savings:                          ${old_cost - total_cost:.3f} ({((old_cost - total_cost) / old_cost * 100):.1f}% less)")
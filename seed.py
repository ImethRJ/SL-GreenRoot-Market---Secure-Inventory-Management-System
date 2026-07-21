import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenroot_market.settings')
django.setup()

from django.contrib.auth.models import User, Group
from inventory.models import Category, Product

def seed():
    # 1. Create categories
    categories = ['Produce', 'Dairy', 'Bakery', 'Beverages', 'Grocery']
    cat_objs = {}
    for cat_name in categories:
        cat, created = Category.objects.get_or_create(name=cat_name)
        cat_objs[cat_name] = cat
        print(f"Category '{cat_name}' - {'Created' if created else 'Exists'}")

    # 2. Create products
    products_data = [
        {
            'sku': 'PROD-SAMBA-01',
            'barcode': '4791234560012',
            'name': 'Araliya Keeri Samba Rice 5kg',
            'category': cat_objs['Grocery'],
            'unit_price': 1450.00,
            'quantity_in_stock': 85,
            'reorder_level': 15,
            'supplier_notes_raw': '# Batch B452\n- Supplier: Araliya Mills\n- Expiry: 2027-12-31\n- Storage: Keep in a cool, dry place.'
        },
        {
            'sku': 'PROD-TEA-02',
            'barcode': '4791234560029',
            'name': 'Watawala Tea 400g',
            'category': cat_objs['Beverages'],
            'unit_price': 850.00,
            'quantity_in_stock': 12,
            'reorder_level': 10,
            'supplier_notes_raw': 'Premium BOPF Ceylon tea blend.'
        },
        {
            'sku': 'PROD-MILK-03',
            'barcode': '4791234560036',
            'name': 'Kotmale Fresh Milk 1L',
            'category': cat_objs['Dairy'],
            'unit_price': 420.00,
            'quantity_in_stock': 8,
            'reorder_level': 12,
            'supplier_notes_raw': '# Dairy Batch\n- Keep refrigerated below 4°C.\n- Expiry: 2026-09-01'
        },
        {
            'sku': 'PROD-BANANA-04',
            'barcode': '4791234560043',
            'name': 'Embul Banana 1kg',
            'category': cat_objs['Produce'],
            'unit_price': 320.00,
            'quantity_in_stock': 40,
            'reorder_level': 15,
            'supplier_notes_raw': 'Freshly harvested from Embilipitiya farms.'
        }
    ]

    for p_data in products_data:
        p, created = Product.objects.get_or_create(
            sku=p_data['sku'],
            defaults=p_data
        )
        print(f"Product '{p.name}' - {'Created' if created else 'Exists'}")

    # 3. Create users
    manager_group = Group.objects.get(name='Manager')
    cashier_group = Group.objects.get(name='Cashier')

    # Manager User
    if not User.objects.filter(username='manager').exists():
        mgr = User.objects.create_user(username='manager', password='pwd', is_staff=True)
        mgr.groups.add(manager_group)
        print("Created Manager User (username: 'manager', password: 'pwd')")
    else:
        print("Manager User already exists")

    # Cashier User
    if not User.objects.filter(username='cashier').exists():
        cshr = User.objects.create_user(username='cashier', password='pwd', is_staff=True)
        cshr.groups.add(cashier_group)
        print("Created Cashier User (username: 'cashier', password: 'pwd')")
    else:
        print("Cashier User already exists")

    # Superuser Admin
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(username='admin', password='pwd')
        print("Created Superuser Admin (username: 'admin', password: 'pwd')")
    else:
        print("Admin User already exists")

if __name__ == '__main__':
    seed()

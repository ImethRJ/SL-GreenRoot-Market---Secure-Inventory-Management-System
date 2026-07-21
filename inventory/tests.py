from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from inventory.models import Category, Product, StockTransaction
from inventory.utils import sanitize_user_markdown

class InventorySecurityAndLogicTests(TestCase):
    def setUp(self):
        # Retrieve user groups created by migration
        self.manager_group = Group.objects.get(name='Manager')
        self.cashier_group = Group.objects.get(name='Cashier')

        # Create test users
        self.manager_user = User.objects.create_user(username='manager', password='pwd')
        self.manager_user.groups.add(self.manager_group)

        self.cashier_user = User.objects.create_user(username='cashier', password='pwd')
        self.cashier_user.groups.add(self.cashier_group)

        self.anonymous_client = Client()

        # Create basic category and product
        self.category = Category.objects.create(name='Produce')
        self.product = Product.objects.create(
            sku='PRD-BANANA-01',
            barcode='4801234567890',
            name='Sri Lankan Ambul Banana',
            category=self.category,
            unit_price=120.00,
            quantity_in_stock=50,
            reorder_level=10,
            supplier_notes_raw='**Organic** bananans from *Matara*.'
        )

    # 1. Dual-Pass Markdown & XSS Sanitization Tests
    def test_markdown_compiles_and_sanitizes(self):
        # Verify basic markdown compilations
        html = sanitize_user_markdown('**Bold** and *Italic*')
        self.assertIn('<strong>Bold</strong>', html)
        self.assertIn('<em>Italic</em>', html)
        
        # Verify strict XSS tag stripping
        xss_input = '## Heading <script>alert("XSS")</script> <iframe src="http://evil.com"></iframe>'
        sanitized = sanitize_user_markdown(xss_input)
        self.assertTrue(sanitized.startswith('<h2>Heading'))
        # script and iframe tags must be completely removed or sanitized
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('<iframe>', sanitized)
        self.assertNotIn('alert', sanitized)

    # 2. Product ORM Logic Tests
    def test_product_low_stock_helper(self):
        # Stock: 50, Reorder: 10 => False
        self.assertFalse(self.product.is_low_stock())

        # Update stock to 10 => True (<= 10)
        self.product.quantity_in_stock = 10
        self.product.save()
        self.assertTrue(self.product.is_low_stock())

        # Update stock to 5 => True
        self.product.quantity_in_stock = 5
        self.product.save()
        self.assertTrue(self.product.is_low_stock())

    # 3. Role-Based Access Control (RBAC) Tests
    def test_manager_access_granted(self):
        client = Client()
        client.login(username='manager', password='pwd')

        # Manager should access dashboard
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Manager should access product create page
        response = client.get(reverse('product_create'))
        self.assertEqual(response.status_code, 200)

        # Manager should access product edit page
        response = client.get(reverse('product_edit', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)

    def test_cashier_access_restricted_on_manager_routes(self):
        client = Client()
        client.login(username='cashier', password='pwd')

        # Cashier can access dashboard
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Cashier can access product list catalog
        response = client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)

        # Cashier can access POS View
        response = client.get(reverse('pos_view'))
        self.assertEqual(response.status_code, 200)

        # Cashier is blocked from creating products (Raises 403 PermissionDenied)
        response = client.get(reverse('product_create'))
        self.assertEqual(response.status_code, 403)

        # Cashier is blocked from editing products
        response = client.get(reverse('product_edit', args=[self.product.id]))
        self.assertEqual(response.status_code, 403)

        # Cashier is blocked from deleting products
        response = client.get(reverse('product_delete', args=[self.product.id]))
        self.assertEqual(response.status_code, 403)

    # 4. Cashier POS Checkout API Transaction Tests
    def test_pos_product_lookup(self):
        client = Client()
        client.login(username='cashier', password='pwd')

        # Lookup by SKU
        response = client.get(reverse('pos_product_lookup'), {'q': 'PRD-BANANA-01'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Sri Lankan Ambul Banana')

        # Lookup by Barcode
        response = client.get(reverse('pos_product_lookup'), {'q': '4801234567890'})
        self.assertEqual(response.status_code, 200)
        
        # Lookup invalid SKU
        response = client.get(reverse('pos_product_lookup'), {'q': 'PRD-INVALID'})
        self.assertEqual(response.status_code, 404)

    def test_pos_checkout_transaction_success(self):
        client = Client()
        client.login(username='cashier', password='pwd')

        # Quantity to purchase: 5
        qty_to_buy = 5
        payload = {
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': qty_to_buy
                }
            ]
        }

        # Send POST checkout request
        response = client.post(
            reverse('pos_checkout'),
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Verify stock decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 45) # 50 - 5 = 45

        # Verify StockTransaction logged
        tx = StockTransaction.objects.filter(product=self.product, type='SALE').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.quantity, -5)
        self.assertEqual(tx.performed_by, self.cashier_user)

    def test_pos_checkout_insufficient_stock(self):
        client = Client()
        client.login(username='cashier', password='pwd')

        # Attempt to buy more than in stock (Buy 60, only 50 in stock)
        payload = {
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 60
                }
            ]
        }

        response = client.post(
            reverse('pos_checkout'),
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient stock', response.json()['error'])

        # Stock should remain unchanged (50)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 50)

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from inventory.utils import sanitize_user_markdown

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True, default='')
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # In LKR
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    supplier_notes_raw = models.TextField(blank=True, help_text="Enter markdown formatted supplier notes.")
    supplier_notes_html = models.TextField(blank=True, editable=False)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    def save(self, *args, **kwargs):
        # Dual-pass processing: compile and sanitize notes before saving
        self.supplier_notes_html = sanitize_user_markdown(self.supplier_notes_raw)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('RESTOCK', 'Restock'),
        ('SALE', 'Sale'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(help_text="Positive for additions, negative for reductions.")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.product.name} ({self.quantity}) by {self.performed_by.username}"

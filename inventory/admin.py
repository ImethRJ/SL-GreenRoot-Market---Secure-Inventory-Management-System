from django.contrib import admin
from inventory.models import Category, Product, StockTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'unit_price', 'quantity_in_stock', 'reorder_level')
    search_fields = ('sku', 'name', 'barcode')
    list_filter = ('category',)
    readonly_fields = ('supplier_notes_html',)

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'performed_by', 'type', 'quantity', 'timestamp')
    list_filter = ('type', 'timestamp')
    readonly_fields = ('timestamp',)


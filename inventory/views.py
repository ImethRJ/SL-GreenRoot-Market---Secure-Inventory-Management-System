import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from inventory.models import Category, Product, StockTransaction
from inventory.forms import ProductForm
from inventory.utils import manager_required, cashier_or_manager_required

@cashier_or_manager_required
def dashboard(request):
    """
    Dashboard Home View
    Displays stock metrics, low stock alert table, and recent transaction log.
    """
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(quantity_in_stock__lte=models.F('reorder_level'))
    total_low_stock = low_stock_products.count()
    
    # Get last 10 transactions
    recent_transactions = StockTransaction.objects.select_related('product', 'performed_by').order_by('-timestamp')[:10]
    
    context = {
        'total_products': total_products,
        'total_low_stock': total_low_stock,
        'low_stock_products': low_stock_products[:10], # show top 10 low stock
        'recent_transactions': recent_transactions,
    }
    return render(request, 'inventory/dashboard.html', context)


@cashier_or_manager_required
def product_list(request):
    """
    Product Catalog View
    Displays all products with search capabilities.
    """
    # Just render the initial page, vanilla JS live search will handle dynamic filtering
    products = Product.objects.select_related('category').order_by('name')
    context = {
        'products': products,
    }
    return render(request, 'inventory/product_list.html', context)


@cashier_or_manager_required
def product_search_api(request):
    """
    API endpoint for Live Search in the catalog.
    Filters products by name, SKU, or barcode.
    """
    query = request.GET.get('q', '').strip()
    products = Product.objects.select_related('category').all()
    
    if query:
        products = products.filter(
            models.Q(name__icontains=query) |
            models.Q(sku__icontains=query) |
            models.Q(barcode__icontains=query)
        )
    
    data = []
    for p in products:
        data.append({
            'id': p.id,
            'sku': p.sku,
            'barcode': p.barcode,
            'name': p.name,
            'category': p.category.name,
            'unit_price': str(p.unit_price),
            'quantity_in_stock': p.quantity_in_stock,
            'is_low_stock': p.is_low_stock(),
            'image_url': p.image.url if p.image else '',
            'edit_url': f'/products/{p.id}/edit/' if (request.user.is_superuser or request.user.groups.filter(name='Manager').exists()) else ''
        })
        
    return JsonResponse({'results': data})


@manager_required
def product_create(request):
    """
    Create Product View (Manager Only)
    Logs an initial 'RESTOCK' transaction if initial stock > 0.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                # Log transaction if initial stock is specified
                if product.quantity_in_stock > 0:
                    StockTransaction.objects.create(
                        product=product,
                        performed_by=request.user,
                        type='RESTOCK',
                        quantity=product.quantity_in_stock
                    )
            messages.success(request, f"Product '{product.name}' was created successfully.")
            return redirect('product_list')
    else:
        form = ProductForm()
        
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


@manager_required
def product_update(request):
    # This matches path parameter by passing pk later, we can fetch using pk.
    pass

# Let's write standard CRUD views:

@manager_required
def product_edit(request, pk):
    """
    Edit Product View (Manager Only)
    Logs a RESTOCK or ADJUSTMENT if quantity_in_stock changed.
    """
    product = get_object_or_404(Product, pk=pk)
    old_stock = product.quantity_in_stock
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            with transaction.atomic():
                updated_product = form.save()
                new_stock = updated_product.quantity_in_stock
                diff = new_stock - old_stock
                
                # Check for changes in stock to audit
                if diff != 0:
                    tx_type = 'RESTOCK' if diff > 0 else 'ADJUSTMENT'
                    StockTransaction.objects.create(
                        product=updated_product,
                        performed_by=request.user,
                        type=tx_type,
                        quantity=diff
                    )
            messages.success(request, f"Product '{updated_product.name}' was updated successfully.")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'inventory/product_form.html', {
        'form': form, 
        'title': 'Edit Product', 
        'product': product,
        'is_edit': True
    })


@manager_required
def product_delete(request, pk):
    """
    Delete Product View (Manager Only)
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Product '{product.name}' deleted successfully.")
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@cashier_or_manager_required
def pos_view(request):
    """
    POS Terminal Checkout View
    """
    return render(request, 'inventory/pos.html')


@cashier_or_manager_required
def pos_product_lookup(request):
    """
    Barcode / SKU lookup endpoint for Cashier POS.
    """
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'error': 'No barcode or SKU provided'}, status=400)
        
    product = Product.objects.filter(
        models.Q(sku__iexact=q) | models.Q(barcode__iexact=q)
    ).first()
    
    if not product:
        return JsonResponse({'error': 'Product not found'}, status=404)
        
    return JsonResponse({
        'id': product.id,
        'sku': product.sku,
        'barcode': product.barcode,
        'name': product.name,
        'unit_price': str(product.unit_price),
        'quantity_in_stock': product.quantity_in_stock,
        'is_low_stock': product.is_low_stock()
    })


@cashier_or_manager_required
@csrf_protect
def pos_checkout(request):
    """
    Deduct stock levels and log a SALE transaction.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        if not items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
            
        with transaction.atomic():
            for item in items:
                product_id = item.get('product_id')
                qty = int(item.get('quantity', 0))
                
                if qty <= 0:
                    return JsonResponse({'error': 'Quantity must be greater than zero'}, status=400)
                    
                product = Product.objects.select_for_update().get(id=product_id)
                
                if product.quantity_in_stock < qty:
                    return JsonResponse({
                        'error': f"Insufficient stock for '{product.name}'. Available: {product.quantity_in_stock}"
                    }, status=400)
                    
                # Deduct stock and save
                product.quantity_in_stock -= qty
                product.save()
                
                # Log transaction
                StockTransaction.objects.create(
                    product=product,
                    performed_by=request.user,
                    type='SALE',
                    quantity=-qty  # Sales are logged as negative stock change
                )
                
        return JsonResponse({'success': True, 'message': 'Checkout transaction processed successfully!'})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

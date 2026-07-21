document.addEventListener('DOMContentLoaded', function() {
    const barcodeInput = document.getElementById('barcode-input');
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    const lookupFeedback = document.getElementById('lookup-feedback');
    const cartTableBody = document.getElementById('cart-table-body');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    
    // Totals Elements
    const summarySubtotal = document.getElementById('summary-subtotal');
    const summaryTotal = document.getElementById('summary-total');
    const cashPaidInput = document.getElementById('cash-paid-input');
    const changeDueOutput = document.getElementById('change-due-output');
    const checkoutBtn = document.getElementById('checkout-btn');
    
    // Get CSRF Token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Cart local state
    let cart = [];

    // Focus input on load
    barcodeInput.focus();

    // Event listener: Add button click
    addToCartBtn.addEventListener('click', handleProductLookup);

    // Event listener: Enter key in input
    barcodeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleProductLookup();
        }
    });

    // Event listener: Clear Cart
    clearCartBtn.addEventListener('click', function() {
        cart = [];
        updateCartUI();
        showFeedback('Cart cleared.', 'info');
    });

    // Event listener: Cash Paid input for change due
    cashPaidInput.addEventListener('input', calculateChange);

    // Event listener: Checkout
    checkoutBtn.addEventListener('click', handleCheckout);

    // Look up product by barcode/SKU
    function handleProductLookup() {
        const query = barcodeInput.value.trim();
        if (!query) {
            showFeedback('Please enter a product SKU or Barcode.', 'error');
            return;
        }

        fetch(`/api/pos/lookup/?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Product not found.');
                    }
                    throw new Error('Server error occurred during lookup.');
                }
                return response.json();
            })
            .then(product => {
                addProductToCart(product);
                barcodeInput.value = '';
                barcodeInput.focus();
                showFeedback(`Added ${product.name} to cart.`, 'success');
            })
            .catch(err => {
                showFeedback(err.message, 'error');
                barcodeInput.select();
            });
    }

    // Add product object to cart state
    function addProductToCart(product) {
        // Check if product is already in cart
        const existingItem = cart.find(item => item.product_id === product.id);
        
        if (existingItem) {
            // Check stock limit
            if (existingItem.quantity + 1 > product.quantity_in_stock) {
                showFeedback(`Cannot add more. Insufficient stock (Available: ${product.quantity_in_stock}).`, 'error');
                return;
            }
            existingItem.quantity += 1;
        } else {
            // Check stock limit
            if (product.quantity_in_stock < 1) {
                showFeedback(`Cannot add. Product '${product.name}' is out of stock.`, 'error');
                return;
            }
            cart.push({
                product_id: product.id,
                sku: product.sku,
                barcode: product.barcode,
                name: product.name,
                unit_price: parseFloat(product.unit_price),
                quantity: 1,
                quantity_in_stock: product.quantity_in_stock
            });
        }
        updateCartUI();
    }

    // Render cart items and update sums
    function updateCartUI() {
        if (cart.length === 0) {
            cartTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-16 text-center text-slate-400">
                        <svg class="h-12 w-12 mx-auto text-slate-200 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        <p class="text-sm font-semibold text-slate-400">Shopping cart is empty. Scan an item to start checkout.</p>
                    </td>
                </tr>
            `;
            summarySubtotal.textContent = 'LKR 0.00';
            summaryTotal.textContent = 'LKR 0.00';
            cashPaidInput.value = '';
            changeDueOutput.textContent = 'LKR 0.00';
            return;
        }

        let html = '';
        let total = 0;

        cart.forEach((item, index) => {
            const itemTotal = item.unit_price * item.quantity;
            total += itemTotal;

            html += `
                <tr class="hover:bg-slate-50/50 transition duration-150">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-semibold text-slate-800">${item.name}</div>
                        <div class="text-[10px] text-slate-400 font-mono">${item.sku}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-medium">
                        LKR ${item.unit_price.toFixed(2)}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                        <input type="number" value="${item.quantity}" min="1" max="${item.quantity_in_stock}"
                               class="w-16 px-2.5 py-1 border border-slate-200 rounded-lg text-slate-800 text-center text-sm font-semibold focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                               data-index="${index}" onchange="window.updateCartQty(${index}, this.value)">
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-slate-900">
                        LKR ${itemTotal.toFixed(2)}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                        <button onclick="window.removeCartItem(${index})" class="text-rose-500 hover:text-rose-700 p-1.5 hover:bg-rose-50 rounded-lg transition duration-150">
                            <svg class="h-4.5 w-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                            </svg>
                        </button>
                    </td>
                </tr>
            `;
        });

        cartTableBody.innerHTML = html;
        summarySubtotal.textContent = `LKR ${total.toFixed(2)}`;
        summaryTotal.textContent = `LKR ${total.toFixed(2)}`;
        calculateChange();
    }

    // Global handles for dynamically generated HTML elements
    window.updateCartQty = function(index, value) {
        let val = parseInt(value);
        const item = cart[index];
        
        if (isNaN(val) || val < 1) {
            val = 1;
        }
        
        if (val > item.quantity_in_stock) {
            showFeedback(`Requested quantity exceeds available stock (${item.quantity_in_stock}).`, 'error');
            val = item.quantity_in_stock;
        }
        
        item.quantity = val;
        updateCartUI();
    };

    window.removeCartItem = function(index) {
        cart.splice(index, 1);
        updateCartUI();
        showFeedback('Item removed from cart.', 'info');
    };

    // Calculate change due
    function calculateChange() {
        const total = parseFloat(summaryTotal.textContent.replace('LKR ', '')) || 0;
        const cashPaid = parseFloat(cashPaidInput.value) || 0;
        
        if (cashPaid >= total && total > 0) {
            const change = cashPaid - total;
            changeDueOutput.textContent = `LKR ${change.toFixed(2)}`;
            changeDueOutput.className = "font-mono font-bold text-emerald-400 text-sm";
        } else {
            changeDueOutput.textContent = 'LKR 0.00';
            changeDueOutput.className = "font-mono font-bold text-slate-500 text-sm";
        }
    }

    // Process POST Checkout
    function handleCheckout() {
        if (cart.length === 0) {
            showFeedback('Your cart is empty. Cannot checkout.', 'error');
            return;
        }

        const total = parseFloat(summaryTotal.textContent.replace('LKR ', ''));
        const cashPaid = parseFloat(cashPaidInput.value) || 0;

        if (cashPaid < total) {
            showFeedback('Cash paid is less than the net total.', 'error');
            return;
        }

        checkoutBtn.disabled = true;
        checkoutBtn.textContent = 'Processing...';

        // Format items payload
        const payload = {
            items: cart.map(i => ({
                product_id: i.product_id,
                quantity: i.quantity
            }))
        };

        fetch('/api/pos/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            if (res.status !== 200) {
                throw new Error(res.body.error || 'Checkout transaction failed.');
            }
            
            // Success
            showFeedback('Checkout completed successfully!', 'success');
            
            // Display alert/pop for confirmation
            alert(`Sale Completed!\nTotal: LKR ${total.toFixed(2)}\nCash Paid: LKR ${cashPaid.toFixed(2)}\nChange Given: LKR ${(cashPaid - total).toFixed(2)}`);
            
            // Reset states
            cart = [];
            updateCartUI();
        })
        .catch(err => {
            showFeedback(err.message, 'error');
        })
        .finally(() => {
            checkoutBtn.disabled = false;
            checkoutBtn.textContent = 'Complete Checkout';
        });
    }

    // Feedback notifications displayer
    function showFeedback(message, type = 'info') {
        lookupFeedback.classList.remove('hidden', 'bg-emerald-50', 'text-emerald-700', 'bg-rose-50', 'text-rose-700', 'bg-sky-50', 'text-sky-700');
        
        lookupFeedback.textContent = message;
        
        if (type === 'success') {
            lookupFeedback.classList.add('bg-emerald-50', 'text-emerald-700');
        } else if (type === 'error') {
            lookupFeedback.classList.add('bg-rose-50', 'text-rose-700');
        } else {
            lookupFeedback.classList.add('bg-sky-50', 'text-sky-700');
        }
        
        lookupFeedback.classList.remove('hidden');
        
        // Hide after 4 seconds
        setTimeout(() => {
            if (lookupFeedback.textContent === message) {
                lookupFeedback.classList.add('hidden');
            }
        }, 4000);
    }
});

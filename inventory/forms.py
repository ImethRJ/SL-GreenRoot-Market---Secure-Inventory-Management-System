from django import forms
from inventory.models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'sku', 'barcode', 'name', 'category', 'unit_price',
            'quantity_in_stock', 'reorder_level', 'supplier_notes_raw', 'image'
        ]
        widgets = {
            'supplier_notes_raw': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write notes in Markdown...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Standard input class
        input_class = (
            "w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-800 "
            "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 "
            "transition duration-150 ease-in-out bg-white/80"
        )
        
        for field_name, field in self.fields.items():
            if field_name == 'image':
                field.widget.attrs.update({
                    'class': (
                        "block w-full text-sm text-slate-500 "
                        "file:mr-4 file:py-2 file:px-4 file:rounded-lg "
                        "file:border-0 file:text-sm file:font-semibold "
                        "file:bg-emerald-50 file:text-emerald-700 "
                        "hover:file:bg-emerald-100 cursor-pointer transition duration-150"
                    )
                })
            elif field_name == 'supplier_notes_raw':
                field.widget.attrs.update({
                    'class': input_class + " font-mono text-sm"
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': "rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4 border-slate-300"
                })
            else:
                field.widget.attrs.update({
                    'class': input_class
                })

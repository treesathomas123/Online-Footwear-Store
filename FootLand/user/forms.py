from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'brand', 'price', 'stock_quantity', 'image', 'size', 'color']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name[0].isupper():
            raise forms.ValidationError("Name must start with a capital letter")
        if not name.isalpha():
            raise forms.ValidationError("Name should not contain symbols")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description.split()) > 100:
            raise forms.ValidationError("Description cannot exceed 100 words")
        return description

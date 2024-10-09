from django import forms
from .models import Product
from .models import UserProfile
class ProductForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('mens', 'Mens'),
        ('womens', 'Womens'),
        ('kids', 'kids'),
    ]

    category = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.Select)

    class Meta:
        model = Product
        fields = ['name', 'description', 'brand', 'price', 'stock_quantity', 'image', 'size', 'color', 'category']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name[0].isupper():
            raise forms.ValidationError("Name must start with a capital letter")
        if not name.replace(" ", "").isalpha():  # Allowing spaces in the name
            raise forms.ValidationError("Name should not contain symbols")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description.split()) > 100:
            raise forms.ValidationError("Description cannot exceed 100 words")
        return description

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'pincode', 'phone', 'state', 'street', 'house_no']

        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your pincode'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your state'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your street'}),
            'house_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your house number'}),
        }

from django import forms
from .models import Product
from .models import UserProfile
from .models import Review


class ProductForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('mens', 'Mens'),
        ('womens', 'Womens'),
        ('kids', 'kids'),
    ]

    category = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.Select)

    class Meta:
        model = Product
        fields = ['name', 'description', 'brand','type', 'price', 'stock_quantity', 'image', 'size', 'color', 'category']

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
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'email', 'rating', 'comment']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email',
                'required': True
            }),
            'rating': forms.RadioSelect(choices=[
                (1, '1 Star'),
                (2, '2 Stars'),
                (3, '3 Stars'),
                (4, '4 Stars'),
                (5, '5 Stars')
            ], attrs={'class': 'star-rating', 'required': True}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...',
                'required': True
            }),
        }

    # Optionally, you can define clean methods for additional validation
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or int(rating) not in range(1, 6):
            raise forms.ValidationError('Please select a valid star rating.')
        return rating

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        return email
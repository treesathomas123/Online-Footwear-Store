from django import forms
from .models import Product
from .models import UserProfile
from .models import Review
from .models import VendorDetails
from .models import Offer


class ProductForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('mens', 'Mens'),
        ('womens', 'Womens'),
        ('kids', 'kids'),
    ]

    category = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.Select)

    class Meta:
        model = Product
        fields = ['name', 'description', 'material', 'brand', 'type', 'price', 'stock_quantity', 'image', 'size', 'color', 'category']

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
    DISTRICT_CHOICES = [
        ('', 'Select District'),
        ('Alappuzha', 'Alappuzha'),
        ('Ernakulam', 'Ernakulam'),
        ('Idukki', 'Idukki'),
        ('Kannur', 'Kannur'),
        ('Kasaragod', 'Kasaragod'),
        ('Kollam', 'Kollam'),
        ('Kottayam', 'Kottayam'),
        ('Kozhikode', 'Kozhikode'),
        ('Malappuram', 'Malappuram'),
        ('Palakkad', 'Palakkad'),
        ('Pathanamthitta', 'Pathanamthitta'),
        ('Thiruvananthapuram', 'Thiruvananthapuram'),
        ('Thrissur', 'Thrissur'),
        ('Wayanad', 'Wayanad'),
    ]

    district = forms.ChoiceField(
        choices=DISTRICT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['address', 'pincode', 'phone', 'state', 'street', 'house_no', 'district']

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
        fields = ['rating', 'comment', 'image']
        
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'rating-input',
                'min': '1',
                'max': '5',
                'step': '1',
                'type': 'range',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or int(rating) not in range(1, 6):
            raise forms.ValidationError('Please select a valid star rating between 1 and 5.')
        return rating

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        return email
    
   
class VendorDetailsForm(forms.ModelForm):
    class Meta:
        model = VendorDetails
        fields = ['profile_image', 'vendor_name', 'shop_name', 'address', 
                 'postal_code', 'phone_number', 'location', 'aadhar_card', 
                 'shop_license']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'phone_number': forms.TextInput(attrs={'type': 'tel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make file fields optional
        self.fields['aadhar_card'].required = False
        self.fields['shop_license'].required = False
        self.fields['profile_image'].required = False

class ReviewReplyForm(forms.ModelForm):
    reply = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Write your reply here...', 'rows': 4}))
    
    class Meta:
        model = Review
        fields = ['reply']

class ReportReviewForm(forms.ModelForm):
    REPORT_REASONS = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('fake', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('other', 'Other')
    ]
    
    report_reason = forms.ChoiceField(
        choices=REPORT_REASONS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    additional_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide additional details...'
        }),
        required=False
    )

    class Meta:
        model = Review
        fields = ['report_reason']

class OfferForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Select start date and time'
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Select end date and time'
    )

    class Meta:
        model = Offer
        fields = ['product', 'offer_type', 'discount_value', 'start_date', 'end_date', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        discount_value = cleaned_data.get('discount_value')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date")

        if discount_value and discount_value <= 0:
            raise forms.ValidationError("Discount value must be greater than 0")

        if cleaned_data.get('offer_type') == 'discount' and discount_value > 100:
            raise forms.ValidationError("Percentage discount cannot exceed 100%")

        return cleaned_data

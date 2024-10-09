from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings  # Use this for the custom user model

# Create your models here.

# Create your models here.
class user_registration(models.Model):
    first_name = models.CharField(max_length=50, default="Anonymous")  # Set a default value
    last_name = models.CharField(max_length=50, default="User")  # You can set a default for last name too
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    def check_password(self, raw_password):
        """Check if the given raw password matches the stored hashed password."""
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        """Hash the password and store it."""
        self.password = make_password(raw_password)

    def save(self, *args, **kwargs):
        """Override the save method to hash the password on creation."""
        if not self.pk and not self.password.startswith('pbkdf2_sha256$'):  # Only hash if it's not already hashed
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        """Return a string representation of the user."""
        return f'{self.first_name} {self.last_name}'
    
    
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('kids', 'Kids'),
        ('mens', 'Mens'),
        ('womens', 'Womens'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    brand = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=20)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)  # New field for category

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(user_registration, on_delete=models.CASCADE)  # Use your custom user model
    address = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=100, null=True, blank=True)
    house_no = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

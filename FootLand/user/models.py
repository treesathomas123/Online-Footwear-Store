from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings  # Use this for the custom user model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.mail import send_mail


# Create your models here.

# Create your models here.
class user_registration(models.Model):
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('vendor', 'Vendor'),
    ]
    
    first_name = models.CharField(max_length=50, default="Anonymous")
    last_name = models.CharField(max_length=50, default="User")
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)


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
    SIZE_CHOICES = [
            ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')
                    ]

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    material = models.TextField(max_length=1000)
    brand = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    size = models.CharField(max_length=20, default='6', null=True, choices=SIZE_CHOICES)  # Allow null if not provided
    color = models.CharField(max_length=20)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name
    
    def get_available_sizes(self):
        # Assuming size is a CharField with choices,
        # return the available sizes based on the SIZE_CHOICES
        return [size[0] for size in self.SIZE_CHOICES]
    
    
    def reduce_stock(self, quantity):
        self.stock_quantity -= quantity
        self.save()



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
    
class Cart(models.Model):
    user = models.ForeignKey(user_registration, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10)  # New field for size
    saved_for_later = models.BooleanField(default=False)  # New field
    def __str__(self):
        return f"{self.user.first_name}'s cart - {self.product.name} (Size: {self.size})"
    
    def total_price(self):
        return self.product.price * self.quantity
    
class SavedItem(models.Model):
    user = models.ForeignKey(user_registration, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_saved = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name}'s saved item - {self.product.name}"

    
class Wishlist(models.Model):
    user = models.ForeignKey(user_registration, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlists')

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate entries

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'
    
class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(user_registration, on_delete=models.CASCADE)
 # Assuming you are using Django's User model
    rating = models.PositiveIntegerField()  # 1 to 5 stars
    comment = models.TextField()
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True)  # Allow null values
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating} stars"
    

class Order(models.Model):
    user = models.ForeignKey(user_registration, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=10)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20)
    order_status = models.CharField(max_length=50, default="Processing")

    def __str__(self):
        return f"Order for {self.product.name} by {self.user.first_name}"
    
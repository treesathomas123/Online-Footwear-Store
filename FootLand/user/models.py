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
        ('delivery_boy', 'Delivery Boy'),  # New user type
    ]
    
    first_name = models.CharField(max_length=50, default="Anonymous")
    last_name = models.CharField(max_length=50, default="User")
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    user_type = models.CharField(max_length=12, choices=USER_TYPE_CHOICES, default='customer')
    is_active = models.BooleanField(default=False)


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
    vendor = models.ForeignKey(
        user_registration, 
        on_delete=models.CASCADE, 
        related_name='products',
        null=True,  # Add this to make it nullable temporarily
        blank=True  # Add this to make it optional in forms
    )

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    MATERIAL_CHOICES = [
        ('leather', 'Leather'),
        ('textiles', 'Textiles'),
        ('synthetics', 'Synthetics'),
        ('rubber', 'Rubber'),
        ('foam', 'Foam'),
        ('plastic', 'Plastic'),
    ]
    
    BRAND_CHOICES = [
        ('adidas', 'Adidas'),
        ('reebok', 'Reebok'),
        ('woodland', 'Woodland'),
        ('skechers', 'Skechers'),
        ('clarks', 'Clarks'),
        ('crocs', 'Crocs'),
        ('red_tape', 'Red Tape'),
        ('sparx', 'Sparx'),
        ('liberty', 'Liberty'),
        ('paragon', 'Paragon'),
        ('bata', 'Bata'),
        ('mochi', 'Mochi'),
        ('metro', 'Metro'),
        ('marc_loire', 'Marc Loire'),
        ('shoetopia', 'Shoetopia'),
        ('xe_looks', 'XE Looks'),
        ('bata_comfit', 'Bata Comfit'),
        ('trase', 'TRASE'),
        ('mosac', 'MOSAC'),
    ]
    
    TYPE_CHOICES = [
        ('casual_shoes', 'Casual Shoes'),
        ('formal_shoes', 'Formal Shoes'),
        ('party_wear', 'Party Wear'),
        ('heels', 'Heels'),
        ('slippers', 'Slippers'),
        ('flats', 'Flats'),
    ]
    
    COLOR_CHOICES = [
        ('black', 'Black'),
        ('white', 'White'),
        ('brown', 'Brown'),
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('grey', 'Grey'),
        ('tan', 'Tan'),
        ('navy', 'Navy'),
        ('multicolor', 'Multicolor'),
    ]

    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    size = models.CharField(max_length=20, default='6', null=True, choices=SIZE_CHOICES)  # Allow null if not provided
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
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
        
      # Add these new methods
    def check_stock_alert(self):
        """Check if stock is low and send alerts."""
        if self.stock_quantity < 5:  # Threshold for low stock
            try:
                self.send_email_alert()
                # Commenting out the WhatsApp alert
                # self.send_whatsapp_alert()  # Remove or comment this line
            except Exception as e:
                print(f"Error sending alerts: {str(e)}")

    def send_email_alert(self):
        """Send email alert to vendor."""
        if self.vendor:
            subject = f"Low Stock Alert - {self.name}"
            message = f"""
            Dear Vendor,

            This is to inform you that the stock for {self.name} is running low.

            Current Stock: {self.stock_quantity}
            Product Details:
            - Brand: {self.brand}
            - Type: {self.type}
            - Size: {self.size}
            - Color: {self.color}

            Please take necessary action to replenish the stock.

            Best regards,
            FootLand Team
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [self.vendor.email],
                    fail_silently=False
                )
                print(f"Stock alert email sent to {self.vendor.email}")
            except Exception as e:
                print(f"Failed to send email: {str(e)}")

   
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
    
# class VendorDetails(models.Model):
#     vendor = models.OneToOneField(
#         'user_registration',
#         on_delete=models.CASCADE,
#         related_name='vendor_details',
#         db_column='vendor_id',  # Explicitly specify the database column name
#         null=False,
#         blank=True
#     )
    
#     vendor_name = models.CharField(max_length=100)
#     shop_name = models.CharField(max_length=100)
#     address = models.TextField()
#     postal_code = models.CharField(max_length=10)
#     phone_number = models.CharField(max_length=15)
#     location = models.CharField(max_length=100)
#     aadhar_card = models.FileField(upload_to='vendor_documents/')
#     shop_license = models.FileField(upload_to='vendor_documents/')
#     shop_photos = models.ManyToManyField('ShopPhoto', blank=True)

#     class Meta:
#         db_table = 'user_vendordetails'  # Specify the exact table name

#     def __str__(self):
#         return f"{self.vendor_name} - {self.shop_name}"

#     def get_aadhar_url(self):
#         if self.aadhar_card:
#             return self.aadhar_card.url
#         return None

#     def get_license_url(self):
#         if self.shop_license:
#             return self.shop_license.url
#         return None

# class ShopPhoto(models.Model):
#     photo = models.ImageField(upload_to='vendor_photos/')

#     def __str__(self):
#         return f"Photo {self.id}"


class VendorDetails(models.Model):
    vendor = models.ForeignKey(
        'user_registration',
        on_delete=models.CASCADE,
        db_column='vendor_id',  # Explicitly specify the column name
        related_name='vendor_details',
        null=True,
        blank=True
    )
    
    vendor_name = models.CharField(max_length=100)
    shop_name = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15)
    location = models.CharField(max_length=255)  # Increased length for full addresses
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    aadhar_card = models.FileField(upload_to='vendor_documents/')
    shop_license = models.FileField(upload_to='vendor_documents/')
    profile_image = models.ImageField(upload_to='vendor_profiles/', null=True, blank=True)
    

    class Meta:
        db_table = 'user_vendordetails'  # Specify the exact table name

    def __str__(self):
        return f"{self.vendor_name} - {self.shop_name}"

    def get_aadhar_url(self):
        if self.aadhar_card:
            return self.aadhar_card.url
        return None

    def get_license_url(self):
        if self.shop_license:
            return self.shop_license.url
        return None
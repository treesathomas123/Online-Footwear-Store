from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from django.db import models

class user_registration(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    # This method can be used to update the password field
    def set_password(self, raw_password):
        self.password = raw_password  # No hashing, storing as plain text

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

 
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    brand = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
 
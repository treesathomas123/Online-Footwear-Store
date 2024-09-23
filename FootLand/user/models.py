from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class user_registration(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()  
    
def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
 
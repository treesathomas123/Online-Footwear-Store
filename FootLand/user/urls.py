from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('cart/', views.cart, name='cart'),
    path('product/', views.product, name='product'),
    path('products_details/', views.products_details, name='products_details'),
    path('products/', views.products, name='products'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'), 
    path('view_customers/', views.view_customers, name='view_customers'),
    path('delete_customer/<int:id>/', views.delete_customer, name='delete_customer'),
    
     path('add-product/', views.add_product, name='add_product'),
      path('view_product/', views.view_product, name='view_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
]
    

     
    
   


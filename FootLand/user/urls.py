from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

from . import views
from .views import product_list  
from .views import add_profile, change_password
urlpatterns = [
    path('', views.home, name='home'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('cart/', views.cart, name='cart'),
   
    path('product/', views.product, name='product'), # home page product
    path('womens/', views.womens, name='womens'), # womens product page
    path('mens/', views.mens, name='mens'),
    path('kids/', views.kids, name='kids'),
     path('search/', views.search, name='search'),  # Add this line for search
    path('products_details/', views.products_details, name='products_details'),
    path('products/', views.products, name='products'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'), 
    path('view_customers/', views.view_customers, name='view_customers'),
    path('delete_customer/<int:id>/', views.delete_customer, name='delete_customer'),
    # Password reset flow
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-code/<str:email>/', views.verify_code, name='verify_code'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
    path('add-product/', views.add_product, name='add_product'),
    path('view_product/', views.view_product, name='view_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('profile/', views.add_profile, name='add_profile'), 
    path('logout/', LogoutView.as_view(), name='logout'), # logout 
    path('products/<str:category>/', product_list, name='product_list'),
     path('change_password/', change_password, name='change_password'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

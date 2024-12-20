from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import add_to_wishlist, wishlist_view, remove_from_wishlist,product_detail
from . import views
from .views import product_list  
from .views import add_profile, change_password
from .views import add_to_cart, view_cart, update_cart, place_order
from .views import billing_details, save_billing_details, billing_details2  # Import the new view
from .views import admin_dashboard, view_orders 

urlpatterns = [
    path('', views.home, name='home'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
   
    path('product/', views.product, name='product'), # home page product
    path('womens/', views.womens, name='womens'), # womens product page
    path('mens/', views.mens, name='mens'),
   # path('kids/', views.kids, name='kids'),
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
    path('logout/', views.logout, name='logout'), # logout 
    path('products/<str:category>/', product_list, name='product_list'),
    path('change_password/', change_password, name='change_password'),
    path('kids/', views.kids_products, name='kids_products'),  # Add this line
    path('kids-products/', views.kids_products, name='kids_products'),
    path('womens-products/', views.womens_products, name='womens_products'),
    path('mens-products/', views.mens_products, name='mens_products'),
    path('add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.view_cart, name='cart'),  # Change 'cart' to 'view_cart'
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart, name='update_cart'),
    path('cart/save_for_later/<int:product_id>/', views.save_for_later, name='save_for_later'),
    path('cart/move_to_cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
    path('remove_saved_item/<int:product_id>/', views.remove_saved_item, name='remove_saved_item'),
    path('order/', views.place_order, name='place_order'),
     path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    #path('confirm-order/', confirm_order, name='confirm_order'),  # Confirm order after verification
    path('analytics/', views.analytics, name='analytics'),
    path('vendors/', views.vendors, name='vendors'),
     path('billing-details/', views.billing_details, name='billing_details'),
    path('save-billing-details/', views.save_billing_details, name='save_billing_details'),
    path('billing-details2/', billing_details2, name='billing_details2'),  # New URL pattern
    path('confirm_order/', views.confirm_order, name='confirm_order'),
    path('confirm_order_final/', views.confirm_order_final, name='confirm_order_final'),
    path('order_summary/', views.order_summary, name='order_summary'),
    path('download-order-summary/', views.download_order_summary, name='download_order_summary'),
    path('online_payment/', views.online_payment, name='online_payment'),  # Add online payment view
    path('my-orders/', views.my_orders, name='my_orders'),
   path('orders/', views.view_orders, name='view_orders'),
    
    
   
   
     
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

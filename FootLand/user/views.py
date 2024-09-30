from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import user_registration
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

def home(request):
    return render(request, 'home.html')
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Check if it's admin login (hardcoded credentials)
        if email == 'admin@gmail.com' and password == 'admin@123':
            # Admin login successful
            return redirect('admin_dashboard')

        try:
            # Check if email exists in the user_registration table
            user_obj = user_registration.objects.get(email=email)

            # Directly compare the plain text password
            if password == user_obj.password:
                # Store user information in the session (custom authentication)
                request.session['user_id'] = user_obj.id
                request.session['user_name'] = f"{user_obj.first_name} {user_obj.last_name}"
                return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid email or password.")
                return redirect('login')

        except user_registration.DoesNotExist:
            messages.error(request, "This account doesn't exist. Please sign up first.")
            return redirect('login')

    return render(request, 'login.html')

def user_dashboard(request):
    # User dashboard view
    return render(request, 'user_dashboard.html')

def admin_dashboard(request):
    # Admin dashboard view
    return render(request, 'admin_dashboard.html')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'signup.html')

        if user_registration.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'signup.html')

        new_user = user_registration(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password)
        )
        new_user.save()

        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')

    return render(request, 'signup.html')

def view_customers(request):
    customers = user_registration.objects.all()  # Fetch all customers
    return render(request, 'view_customers.html', {'customers': customers})



def delete_customer(request, id):
    try:
        customer = user_registration.objects.get(id=id)
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
    except user_registration.DoesNotExist:
        messages.error(request, 'Customer does not exist!')
    
    return redirect('view_customers')




def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product successfully added!')
            return redirect('add_product')
        else:
            messages.error(request, 'Error adding product. Please check the form.')
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

def view_product(request):
    products = Product.objects.all()
    return render(request, 'view_product.html', {'products': products})

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('view_product')

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('view_product')
    else:
        form = ProductForm(instance=product)

    return render(request, 'edit_product.html', {'form': form, 'product': product})

@login_required
def cart(request):
    return render(request, 'cart.html')

@login_required
def product(request):
    return render(request, 'product.html')

@login_required
def products_details(request):
    return render(request, 'products-details.html')

@login_required
def products(request):
    return render(request, 'products.html')

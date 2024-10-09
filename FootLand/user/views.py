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
import random 
from django.urls import reverse
from django.core.mail import send_mail
from .models import UserProfile
from .forms import ProfileForm

# Dictionary to temporarily store user pins
user_pins = {}


def home(request):
    return render(request, 'home.html')


def user_dashboard(request):
    user_id = request.session.get('user_id')
    first_name = request.session.get('first_name', "Guest")
    last_name = request.session.get('last_name', "")

    # Pass the user's first name, last name, and ID to the template
    return render(request, 'user_dashboard.html', {
        'first_name': first_name,
        'last_name': last_name,
        'user_id': user_id
    })



def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Check if it's admin login (hardcoded credentials)
        if email == 'admin@gmail.com' and password == 'admin@123':
            return redirect('admin_dashboard')

        try:
            user_obj = user_registration.objects.get(email=email)

            # Use check_password to compare the input password with the stored hashed password
            if check_password(password, user_obj.password):
                # Store user information in the session
                request.session['user_id'] = user_obj.id
                request.session['username'] = user_obj.first_name  # Assuming you store full names as first name
                return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid email or password.")
                return redirect('login')

        except user_registration.DoesNotExist:
            messages.error(request, "This account doesn't exist. Please sign up first.")
            return redirect('login')

    return render(request, 'login.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = user_registration.objects.get(email=email)  # Ensure this model is correct
            # Generate a random 4-digit code
            code = random.randint(1000, 9999)
            user_pins[email] = code

            # Send email with the code
            send_mail(
                'Password Reset Code',
                f'Your password reset code is {code}.',
                'admin@yourdomain.com',  # Change to your domain
                [email],
                fail_silently=False,
            )
            # Redirect to the verification page
            messages.success(request, 'A reset code has been sent to your email.')
            verify_code_url = reverse('verify_code', kwargs={'email': email})
            return redirect(verify_code_url)
        except user_registration.DoesNotExist:  # Updated model name
            messages.error(request, 'Invalid email address.')
    return render(request, 'forgot_password.html')

# Verify code view
def verify_code(request, email):
    if request.method == 'POST':
        entered_code = request.POST.get('pin')
        correct_code = user_pins.get(email)

        if correct_code and str(entered_code) == str(correct_code):
            # Redirect to reset password page
            return redirect('reset_password', email=email)
        else:
            messages.error(request, 'Invalid code. Please try again.')

    return render(request, 'verify_code.html', {'email': email})


# Reset password view
def reset_password(request, email):
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if new_password1 == new_password2:
            try:
                user = user_registration.objects.get(email=email)  # Updated model name
                user.set_password(new_password1)  # Use set_password to hash the password
                user.save()  # Save the changes to the database
                messages.success(request, 'Password has been reset successfully.')
                return redirect('login')
            except user_registration.DoesNotExist:  # Updated model name
                messages.error(request, 'Invalid user.')
        else:
            messages.error(request, 'Passwords do not match.')
    return render(request, 'reset_password.html', {'email': email})

def user_dashboard(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = user_registration.objects.get(id=user_id)
            first_name = user.first_name
        except user_registration.DoesNotExist:
            first_name = 'Guest'
    else:
        first_name = 'Guest'

    return render(request, 'user_dashboard.html', {'first_name': first_name})



def logout(request):
    request.session.flush()  # Clears all session data
    return redirect('login')


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
        return redirect('user_dashboard')

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



from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ProductForm  # Make sure to import your form
# from .models import Product  # Optional if needed for further reference

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Product successfully added!')
                return redirect('add_product')
            except Exception as e:
                messages.error(request, f'Error adding product: {e}')
        else:
            # Log the form errors for debugging
            messages.error(request, 'Error adding product. Please check the form.')
            for field, errors in form.errors.items():
                print(f"{field}: {errors}")
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})




def view_product(request):
    products = Product.objects.all()  # Fetch all products from the database
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
    # This view can handle displaying cart items
    return render(request, 'cart.html')  # Create a simple cart template
@login_required
def product(request):
   return render(request, 'product.html')


def womens(request):
    return render(request, 'womens.html')


def mens(request):
    return render(request, 'mens.html')


def kids(request):
    return render(request, 'kids.html')

@login_required
def products_details(request):
    return render(request, 'products-details.html')

@login_required
def products(request):
    return render(request, 'products.html')

def search(request):
    query = request.GET.get('q')  # Fetch the search query from the GET request
    if query:
        products = Product.objects.filter(name__icontains=query)  # Filter products by name
    else:
        products = Product.objects.all()  # If no query, display all products

    context = {
        'products': products,
        'query': query
    }
    return render(request, 'search_results.html', context)

from django.core.paginator import Paginator

def search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()

    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'query': query
    }
    return render(request, 'search_results.html', context)


def add_profile(request):
    user_id = request.session.get('user_id')  # Get the user ID from the session

    # Check if the user ID is set in the session
    if user_id:
        try:
            user = user_registration.objects.get(id=user_id)  # Get the user instance
        except user_registration.DoesNotExist:
            return redirect('login')  # Redirect if the user does not exist

        # Retrieve or create the user profile
        profile, created = UserProfile.objects.get_or_create(user=user)

        if request.method == 'POST':
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('add_profile')  # Redirect to the same page after saving
        else:
            form = ProfileForm(instance=profile)

        return render(request, 'add_profile.html', {
            'form': form,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        })

    # If the user is not authenticated, redirect to the login page
    return redirect('login')


def change_password(request):
    user_id = request.session.get('user_id')  # Assuming you are storing user ID in session
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            # Hash the password before saving it
            hashed_password = make_password(new_password)
            # Update password in the database
            user_registration.objects.filter(id=user_id).update(password=hashed_password)
            messages.success(request, 'Password changed successfully!')
            return redirect('add_profile')  # Redirect to the profile page or any other page
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'change_password.html', {})


def product_list(request, category):
    products = Product.objects.filter(category=category)  # Fetch products based on the category
    return render(request, 'product_list.html', {'products': products, 'category': category})
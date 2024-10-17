from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import user_registration
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import Product,Cart,Wishlist, Review
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
import random 
from django.urls import reverse
from django.core.mail import send_mail
from .models import UserProfile
from .forms import ProfileForm
from django.http import JsonResponse
#from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.http import HttpResponseRedirect
from .forms import ReviewForm
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

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

@never_cache
def user_dashboard(request):
    if 'user_id' in request.session:
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
    else:
        return redirect('login')



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

        # Customized welcome email
        subject = 'Welcome to Our Footland!'
        message = f"""
        Hi {first_name},

        Welcome to our community! We are thrilled to have you as a part of our website. 

        Whether you're here to shop for your favorite items or discover something new, we strive to provide the best experience possible. Here are a few things you can do now that you're registered:

        - Browse through our exclusive products and deals.
        - Create wishlists and share them with your friends.
        - Leave reviews for products you've purchased to help others in their buying journey.

        Should you ever need assistance or have any questions, feel free to reach out to our support team at support@footland.com. We're always here to help.

        Thank you once again for joining us, and we hope you enjoy your time with us!

        Best regards,
        The Team

        P.S. Don't forget to follow us on social media for the latest updates and offers!
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, 'Registration successful! Please check your email for a warm welcome.')
        except Exception as e:
            messages.error(request, f'Registration successful, but email failed to send: {str(e)}')

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
            return redirect('view_product')  # Redirect to the product view page after saving
    else:
        form = ProductForm(instance=product)

    return render(request, 'edit_product.html', {'form': form, 'product': product})


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

#kids product

def kids_products(request):
    # Filter products by category 'kids'
    products = Product.objects.filter(category='kids')

    # Apply filters based on GET parameters
    price = request.GET.get('price')
    color = request.GET.get('color')
    size = request.GET.get('size')
    brand = request.GET.get('brand')
    
    type = request.GET.get('type')

    if price:
        products = products.filter(price__lte=price)  # Filter products within price range
    if color:
        products = products.filter(color=color)  # Filter products by color
    if size:
        products = products.filter(size=size)  # Filter products by size
    if brand:
        products = products.filter(brand=brand)  # Filter products by brand
    
    if type:
        products = products.filter(type=type)  # Filter products by brand

    context = {
        'products': products,
    }
    return render(request, 'kids_products.html',{'products': products})

#womens product

def womens_products(request):
    # Filter products by category 'kids'
    products = Product.objects.filter(category='womens')

    # Apply filters based on GET parameters
    price = request.GET.get('price')
    color = request.GET.get('color')
    size = request.GET.get('size')
    brand = request.GET.get('brand')
    type = request.GET.get('type')
    

    if price:
        products = products.filter(price__lte=price)  # Filter products within price range
    if color:
        products = products.filter(color=color)  # Filter products by color
    if size:
        products = products.filter(size=size)  # Filter products by size
    if brand:
        products = products.filter(brand=brand)  # Filter products by brand
    if type:
        products = products.filter(type=type)  # Filter products by brand


    context = {
        'products': products,
    }
    return render(request, 'womens_products.html', context)


#mens product

def mens_products(request):
    # Filter products by category 'kids'
    products = Product.objects.filter(category='mens')

    # Apply filters based on GET parameters
    price = request.GET.get('price')
    color = request.GET.get('color')
    size = request.GET.get('size')
    brand = request.GET.get('brand')
    type = request.GET.get('type')

    if price:
        products = products.filter(price__lte=price)  # Filter products within price range
    if color:
        products = products.filter(color=color)  # Filter products by color
    if size:
        products = products.filter(size=size)  # Filter products by size
    if brand:
        products = products.filter(brand=brand)  # Filter products by brand
    if type:
        products = products.filter(type=type)  # Filter products by brand


    context = {
        'products': products,
    }
    return render(request, 'mens_products.html', context)




def add_to_cart(request, product_id):
    print(f"User authenticated: {request.user.is_authenticated}")  # Debug
    if 'user_id' in request.session:
        user_id = request.session['user_id']  # Get the logged-in user ID from session
        user = get_object_or_404(user_registration, id=user_id)
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.success(request, f'{product.name} has been added to your cart!')

        return redirect('cart')
    else:
        messages.error(request, "You need to log in to add items to the cart.")
        return redirect('login')


def view_cart(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']  # Get the logged-in user ID from session
        user = get_object_or_404(user_registration, id=user_id)
        cart_items = Cart.objects.filter(user=user)

        # Calculate total amount for the items in the cart
        total_amount = sum(item.total_price() for item in cart_items)

        # Define your shipping charge and platform fee
        shipping_charge = 50  # You can modify this logic as needed
        platform_fee = 20     # You can modify this logic as needed

        # Prepare context with all necessary variables
        context = {
            'cart_items': cart_items,
            'total_amount': total_amount,
            'shipping_charge': shipping_charge,
            'platform_fee': platform_fee,
        }

        return render(request, 'cart.html', context)
    else:
        messages.error(request, "You need to log in to view your cart.")
        return redirect('login')
    

def remove_from_cart(request, product_id):
    # Get the logged-in user ID from session
    if 'user_id' in request.session:
        user_id = request.session['user_id']  # Retrieve user ID from session
        user = get_object_or_404(user_registration, id=user_id)

        # Get the cart item for the user and the specific product, then delete it
        cart_item = get_object_or_404(Cart, user=user, product__id=product_id)
        cart_item.delete()
        
        # Optionally, display a success message
        messages.success(request, 'Item removed from your cart.')
    else:
        messages.error(request, "You need to log in to remove items from your cart.")
        return redirect('login')

    # Redirect back to the cart page after removing the item
    return redirect('cart')

def update_cart(request, cart_item_id):
    if request.method == "POST":
        user_id = request.session['user_id']  # Get the logged-in user ID from session
        user = get_object_or_404(user_registration, id=user_id)
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=user)
        quantity = request.POST.get('quantity')
        if quantity and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
            messages.success(request, "Cart updated successfully!")
        else:
            messages.error(request, "Invalid quantity.")
    return redirect('cart')  # Redirect back to the cart view

def place_order(request):
    # Logic for placing an order (omitted for brevity)
    messages.success(request, "Your order has been placed successfully!")
    return redirect('home')  # Redirect to the homepage or order confirmation page


def add_to_wishlist(request):
    user_id = request.session['user_id']  # Get the logged-in user ID from session
    user = get_object_or_404(user_registration, id=user_id)
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        print(product_id)
        product = get_object_or_404(Product, pk=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
        if created:
            # Optionally, add a success message
            print(f'{product.name} added to wishlist.')
        else:
            # Optionally, add an error message
            print(f'{product.name} is already in your wishlist.')
        return redirect('kids_products')  # Redirect back to the products page

def wishlist_view(request):
    user_id = request.session['user_id']  # Get the logged-in user ID from session
    user = get_object_or_404(user_registration, id=user_id)
    wishlist_items = Wishlist.objects.filter(user=user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

def remove_from_wishlist(request, product_id):
    # Get the wishlist item and delete it
    user_id = request.session['user_id']  # Get the logged-in user ID from session
    user = get_object_or_404(user_registration, id=user_id)
    wishlist_item = get_object_or_404(Wishlist, user=user, product__id=product_id)
    wishlist_item.delete()
    return redirect('wishlist')  # Redirect to the wishlist page


def product_detail(request, product_id):
    # Fetch the product details
    logger.debug(f"Fetching product with ID: {product_id}")
    
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # Handle the adding to cart logic
        user = request.user  # Get the logged-in user
        if user.is_authenticated:  # Check if the user is authenticated
            quantity = request.POST.get('quantity', 1)  # Get the quantity from the form
            cart_item, created = Cart.objects.get_or_create(user=user, product=product)
            cart_item.quantity += int(quantity)  # Increase the quantity
            cart_item.save()  # Save the cart item
            return redirect('cart')  # Redirect to the cart page

    return render(request, 'product_detail.html', {'product': product})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Create a review but don't save it to the database yet
            review = form.save(commit=False)
            review.product = product  # Associate review with the product
            review.user = request.user  # Set the user to the current user
            review.save()  # Now save it to the database
            messages.success(request, "Your review has been submitted successfully!")
            return redirect('product_detail', product_id=product_id)
        else:
            messages.error(request, "There was an error in your review. Please check the form.")
    
    else:
        form = ReviewForm()

    return render(request, 'product_detail.html', {'product': product, 'form': form})

#def add_review(request, product_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        product = get_object_or_404(Product, id=product_id)

        # Create and save the review
        Review.objects.create(
            product=product,
            name=name,
            email=email,
            rating=int(rating),
            comment=comment
        )
        return redirect('product_detail', product_id=product.id)  # Redirect to product detail page

    return redirect('product_detail', product_id=product_id)  # Handle GET request by redirecting #

#def confirm_order(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        
        # Debugging: Print user_id to check if it's correctly set
        print(f"User ID from session: {user_id}")

        if user_id is None:
            messages.error(request, "User not logged in.")
            return redirect('login')  # Redirect to login if user_id is None

        try:
            user_profile = UserProfile.objects.get(user_id=user_id)  # Fetch user profile
        except UserProfile.DoesNotExist:
            messages.error(request, "UserProfile matching query does not exist.")
            return redirect('add_profile')  # Redirect to profile creation if user_profile does not exist

        # Update the user profile with the new data
        user_registration.first_name = request.POST.get('first_name')
        user_registration.last_name = request.POST.get('last_name')
        user_registration.email = request.POST.get('email')
        user_profile.address = request.POST.get('address')
        user_profile.pincode = request.POST.get('pincode')
        user_profile.phone = request.POST.get('phone')
        user_profile.save()

        # Here you would place your order logic
        # ...

        messages.success(request, "Your order has been placed successfully!")
        return redirect('home')  # Redirect to home or any other page after order is confirmed

    return redirect('cart')  # Redirect back to the cart if the method is not POST

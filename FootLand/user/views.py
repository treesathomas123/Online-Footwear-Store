from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import user_registration, DeliveryBoy, DeliveryAssignment, Order
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import Product,Cart,Wishlist, Review,Order
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
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.http import HttpResponseRedirect
from .forms import ReviewForm
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from decimal import Decimal  # Add this import
from django.db.models import Q
from django.contrib.auth import logout
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.template.loader import render_to_string
from .models import VendorDetails  # Ensure you have a model to store vendor details
from django.core.files.storage import FileSystemStorage
import os
from .forms import ProductForm, VendorDetailsForm
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import google.generativeai as genai
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta, date
import random
import string
from .models import DeliveryBoyProfile
from django.core.paginator import Paginator
from django.template.defaulttags import register
from django.db.models import Exists, OuterRef
import speech_recognition as sr
from PIL import Image
import torch
from torchvision import transforms
import base64
import io

logger = logging.getLogger(__name__)

# Dictionary to temporarily store user pins
user_pins = {}

# Set your Gemini API Key
API_KEY = "AIzaSyDWn4zpv79RDS6Yz2JkEto_-7Hq3dYlvFg"

# Configure the Generative AI client
genai.configure(api_key=API_KEY)

@register.filter
def split(value, key):
    """
    Returns the value turned into a list split at key.
    """
    return value.split(key)

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

        # Check if it's admin login
        if email == 'admin@gmail.com' and password == 'admin@123':
            request.session['user_type'] = 'admin'
            return redirect('admin_dashboard')

        try:
            user_obj = user_registration.objects.get(email=email)
            if check_password(password, user_obj.password):
                # Store ALL necessary session data
                request.session['user_id'] = user_obj.id
                request.session['username'] = user_obj.first_name
                request.session['user_type'] = user_obj.user_type
                request.session['email'] = user_obj.email
                request.session.modified = True  # Force session save
                
                print(f"Login successful - Session data: {request.session.items()}")  # Debug print
                
                # Updated redirect logic
                if user_obj.user_type == 'vendor':
                    return redirect('vendor_dashboard')
                elif user_obj.user_type == 'delivery_boy':
                    return redirect('delivery_boy_dashboard')  # Make sure this URL pattern exists
                return redirect('user_dashboard')

            else:
                messages.error(request, "Invalid email or password.")
                return redirect('login')

        except user_registration.DoesNotExist:
            messages.error(request, "This account doesn't exist.")
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

        # Get the 8 most recent products
        latest_products = Product.objects.all().order_by('-id')[:8]
        
        context = {
            'first_name': first_name,
            'latest_products': latest_products,
        }
        return render(request, 'user_dashboard.html', context)
    else:
        return redirect('login')



def logout(request):
    request.session.flush()  # Clears all session data
    return redirect('login')

def admin_dashboard(request):
    total_products = Product.objects.count()
    total_customers = user_registration.objects.filter(user_type='customer').count()
    total_vendors = user_registration.objects.filter(user_type='vendor').count()  # Count all vendors  # You'll need to implement this based on your vendor model
    total_orders = Order.objects.count() # Assuming each unique user in Cart represents an order

    context = {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'total_orders': total_orders,
    }
    return render(request, 'admin_dashboard.html', context)


def signup(request):
    user_type = None 
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')  # New field for user type

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
            password=make_password(password),
            user_type=user_type  # Set user type
        )
    if user_type == 'customer':
            # Save customer and send welcome email  
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
            messages.success(request, 'Registration successful! Please check your mail!!.')
        except Exception as e:
            messages.error(request, f'Registration successful, but email failed to send: {str(e)}')

        return redirect('user_dashboard')
    
    elif user_type == 'vendor':
            # Save vendor and send approval email
            new_user.save()
            subject = 'Vendor Registration Pending Approval'
            message = f"Hi {first_name},\n\nThank you for registering as a vendor. Please fill out the following form: http://127.0.0.1:8000/submit_vendor_details/"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Registration successful! Please check your mail for further instructions.')
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

def approve_vendor(request, vendor_id):
    vendor = user_registration.objects.get(id=vendor_id)
    vendor.is_active = True  # Activate the vendor
    vendor.save()

    # Send email to vendor with Google Form link
    subject = 'Vendor Approval'
    message = f"Hi {vendor.first_name},\n\nYour vendor account has been approved. Please fill out the following form: [Google Form Link]"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [vendor.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        messages.success(request, 'Vendor approved and email sent!')
    except Exception as e:
        messages.error(request, f'Vendor approved, but email failed to send: {str(e)}')

    return redirect('view_vendors')

def view_vendors(request):
    vendor_details = VendorDetails.objects.select_related('vendor').all()
    
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor_id')
        action = request.POST.get('action')
        
        if vendor_id and action:
            try:
                # Get the vendor directly
                vendor = user_registration.objects.get(id=int(vendor_id))
                
                if action == 'activate':
                    # Update both is_active and user_type
                    vendor.is_active = True
                    vendor.user_type = 'vendor'
                    vendor.save()
                    
                    # Debug print
                    print(f"Activating vendor {vendor.id}: Status={vendor.is_active}, Type={vendor.user_type}")
                    
                    messages.success(request, f'Vendor {vendor.first_name} has been activated.')
                    
                elif action == 'deactivate':
                    vendor.is_active = False
                    vendor.save()
                    
                    # Debug print
                    print(f"Deactivating vendor {vendor.id}: Status={vendor.is_active}")
                    
                    messages.success(request, f'Vendor {vendor.first_name} has been deactivated.')
                
            except user_registration.DoesNotExist:
                messages.error(request, "Vendor not found.")
                print(f"Vendor not found: {vendor_id}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                print(f"Error processing vendor {vendor_id}: {str(e)}")
    
    # Refresh the queryset after changes
    vendor_details = VendorDetails.objects.select_related('vendor').all()
    
    # Debug print all vendors
    for detail in vendor_details:
        if detail.vendor:
            print(f"Vendor {detail.vendor.id}: {detail.vendor.first_name} - Active: {detail.vendor.is_active}")
    
    context = {
        'vendor_details': vendor_details,
    }
    return render(request, 'view_vendors.html', context)


    return render(request, 'view_vendors.html', {'vendors': vendors, 'vendor_details': vendor_details})

def activate_vendor(request, vendor_id):
    try:
        vendor = user_registration.objects.get(id=vendor_id)
        vendor.is_active = True
        vendor.user_type = 'vendor'  # Ensure user type is set
        vendor.save()
        
        # Debug print
        print(f"Activated vendor {vendor_id}: Status={vendor.is_active}, Type={vendor.user_type}")
        
        # Send email to vendor
        try:
            send_mail(
                'Account Activated - Footland',
                f'Dear {vendor.first_name},\n\nYour vendor account has been activated. You can now login to your dashboard.',
                settings.DEFAULT_FROM_EMAIL,
                [vendor.email],
                fail_silently=False,
            )
            messages.success(request, f'Vendor {vendor.first_name} has been activated and notified via email.')
        except Exception as e:
            messages.warning(request, f'Vendor activated but email notification failed: {str(e)}')
            print(f"Email failed for vendor {vendor_id}: {str(e)}")
    
    except user_registration.DoesNotExist:
        messages.error(request, "Vendor not found.")
        print(f"Vendor not found: {vendor_id}")
    except Exception as e:
        messages.error(request, f"Error activating vendor: {str(e)}")
        print(f"Error activating vendor {vendor_id}: {str(e)}")
    
    return redirect('view_vendors')

def deactivate_vendor(request, vendor_id):
    try:
        vendor = user_registration.objects.get(id=vendor_id)
        vendor.is_active = False
        vendor.save()
        
        # Debug print
        print(f"Deactivated vendor {vendor_id}: Status={vendor.is_active}")
        
        # Send email to vendor
        try:
            send_mail(
                'Account Deactivated - Footland',
                f'Dear {vendor.first_name},\n\nYour vendor account has been deactivated. Please contact support for more information.',
                settings.DEFAULT_FROM_EMAIL,
                [vendor.email],
                fail_silently=False,
            )
            messages.success(request, f'Vendor {vendor.first_name} has been deactivated and notified via email.')
        except Exception as e:
            messages.warning(request, f'Vendor deactivated but email notification failed: {str(e)}')
            print(f"Email failed for vendor {vendor_id}: {str(e)}")
    
    except user_registration.DoesNotExist:
        messages.error(request, "Vendor not found.")
        print(f"Vendor not found: {vendor_id}")
    except Exception as e:
        messages.error(request, f"Error deactivating vendor: {str(e)}")
        print(f"Error deactivating vendor {vendor_id}: {str(e)}")
    
    return redirect('view_vendors')


def submit_vendor_details(request):
    print("Starting submit_vendor_details")  # Debug print
    print(f"Session data: {request.session.items()}")  # Debug print
    
    try:
        # Always get the most recently registered vendor first
        user = user_registration.objects.filter(
            user_type='vendor',
            is_active=False
        ).order_by('-id').first()  # Changed to order_by('-id').first() for clarity
        
        if not user:
            messages.error(request, "No pending vendor registration found")
            return redirect('login')
            
        # Update session with the most recent vendor's details
        request.session['user_id'] = user.id
        request.session['username'] = user.first_name
        request.session['user_type'] = user.user_type
        request.session['email'] = user.email
        request.session.modified = True

        print(f"Found most recent vendor: {user.first_name}, ID: {user.id}, Email: {user.email}")  # Debug print

        if request.method == 'POST':
            try:
                vendor_details = VendorDetails(
                    vendor=user,
                    vendor_name=user.first_name,  # Using the correct vendor's name
                    shop_name=request.POST.get('shop_name'),
                    address=request.POST.get('address'),
                    postal_code=request.POST.get('postal_code'),
                    phone_number=request.POST.get('phone_number'),
                    location=request.POST.get('location'),
                    aadhar_card=request.FILES['aadhar_card'],
                    shop_license=request.FILES['shop_license']
                )
                vendor_details.save()
                print(f"Created vendor details for: {user.first_name}")  # Debug print

                messages.success(request, 'Vendor details submitted successfully! Awaiting approval.')
                return redirect('vendor')

            except Exception as e:
                print(f"Error creating vendor details: {str(e)}")  # Debug print
                messages.error(request, f"Error submitting vendor details: {str(e)}")

        # For GET request
        context = {
            'user': user,
            'vendor_name': user.first_name,  # Using the correct vendor's name
            'is_logged_in': True
        }
        return render(request, 'vendor_details.html', context)

    except Exception as e:
        print(f"Error in submit_vendor_details: {str(e)}")  # Debug print
        messages.error(request, "Error accessing vendor details")
        return redirect('login')

def delivery_boy_dashboard(request):
    if 'email' not in request.session:
        return redirect('login')
    
    delivery_boy = get_object_or_404(DeliveryBoy, email=request.session['email'])
    context = {
        'delivery_boy': delivery_boy
    }
    return render(request, 'delivery_boy_dashboard.html', context)

# def active_deliveries(request):

def active_deliveries(request):
    if 'email' not in request.session:
        return redirect('login')
   
    delivery_boy = get_object_or_404(DeliveryBoy, email=request.session['email'])
    today = date.today()
    
    # Get all undelivered assignments (including from previous days)
    active_deliveries = DeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        delivery_status__in=['pending', 'packed', 'dispatched', 'out_for_delivery']
    ).select_related('order')
    
    # Count today's active assignments
    todays_assignments_count = active_deliveries.count()
    
    # Auto-assign new orders if less than 10 deliveries
    if todays_assignments_count < 10:
        delivery_boy_district = delivery_boy.profile.district
        
        # Check for existing assignments
        has_assignment = DeliveryAssignment.objects.filter(
            order=OuterRef('pk')
        )
        
        # Find unassigned orders in the same district
        unassigned_orders = Order.objects.filter(
            user__userprofile__district=delivery_boy_district,
            delivery_status='Processing'
        ).annotate(
            has_delivery=Exists(has_assignment)
        ).filter(
            has_delivery=False
        )[:10 - todays_assignments_count]
        
        # Create new assignments
        for order in unassigned_orders:
            DeliveryAssignment.objects.create(
                order=order,
                delivery_boy=delivery_boy,
                delivery_status='pending',
                assigned_date=today  # Set today's date for new assignments
            )
    
    # Group deliveries by date
    grouped_deliveries = {}
    for assignment in active_deliveries:
        date_str = assignment.assigned_date.strftime('%Y-%m-%d')
        if date_str not in grouped_deliveries:
            grouped_deliveries[date_str] = []
        grouped_deliveries[date_str].append(assignment)
    
    context = {
        'grouped_deliveries': grouped_deliveries,
        'delivery_count': todays_assignments_count,
        'remaining_slots': max(0, 10 - todays_assignments_count),
        'today': today.strftime('%Y-%m-%d')
    }
    
    return render(request, 'active_deliveries.html', context)

def update_delivery_status(request, assignment_id):
    if request.method == 'POST' and 'email' in request.session:
        status = request.POST.get('status')
        assignment = get_object_or_404(DeliveryAssignment, id=assignment_id)
        
        status_flow = {
            'pending': 'Processing',
            'packed': 'Packed',
            'dispatched': 'Dispatched',
            'out_for_delivery': 'Out for Delivery',
            'delivered': 'Delivered',
            'failed': 'Failed'
        }
        
        if status in status_flow:
            # Update both assignment and order status
            old_status = assignment.delivery_status
            assignment.delivery_status = status
            assignment.save()
            
            order = assignment.order
            order.delivery_status = status_flow[status]
            order.save()
            
            if status in ['delivered', 'failed']:
                messages.success(request, f"Order #{order.id} has been marked as {status_flow[status]}")
            else:
                messages.success(request, f"Order #{order.id} status updated from {old_status} to {status}")
    
    return redirect('active_deliveries')

from django.db.models import Count, Sum

def analytics(request):
    # User distribution data
    customer_count = user_registration.objects.filter(user_type='customer').count()
    admin_count = user_registration.objects.filter(user_type='admin').count()

    # Orders distribution by category
    order_data = (
        Order.objects
        .values('product__category')
        .annotate(count=Count('product__category'))
    )
    order_data_dict = {item['product__category']: item['count'] for item in order_data}

    # Best-selling products data
    best_selling_products = (
        Order.objects
        .values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )

    context = {
        'customer_count': customer_count,
        'admin_count': admin_count,
        'order_data': json.dumps(order_data_dict),
        'best_selling_products': best_selling_products,
    }

    return render(request, 'analytics.html', context)

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
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')
    search_type = request.GET.get('type', 'text')
    
    products = Product.objects.all()
    
    if search_type == 'text' and query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )
    
    elif search_type == 'voice':
        # Handle voice search
        audio_file = request.FILES.get('audio')
        if audio_file:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                try:
                    query = recognizer.recognize_google(audio)
                    products = products.filter(
                        Q(name__icontains=query) |
                        Q(description__icontains=query)
                    )
                except sr.UnknownValueError:
                    return JsonResponse({'error': 'Could not understand audio'})
    
    elif search_type == 'image':
        # Handle image search
        image_file = request.FILES.get('image')
        if image_file:
            products = search_by_image(image_file, products)
    
    # Handle category filtering
    if category and category != 'all':
        products = products.filter(category=category)
    
    # Get all unique categories, types, brands for filters
    all_categories = Product.CATEGORY_CHOICES
    all_types = Product.TYPE_CHOICES
    all_brands = Product.BRAND_CHOICES
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'category': category,
        'total_results': products.count(),
        'all_categories': all_categories,
        'all_types': all_types,
        'all_brands': all_brands
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON response for AJAX requests
        return JsonResponse({
            'html': render_to_string('product_list_partial.html', context),
            'total': products.count()
        })
    
    return render(request, 'search_results.html', context)

def search_by_image(image_file, products):
    # Convert uploaded image to PIL Image
    image = Image.open(image_file)
    
    # Implement your image similarity search logic here
    # This is a simplified example
    similar_products = []
    for product in products:
        if product.image:
            similarity = compare_images(image, Image.open(product.image.path))
            if similarity > 0.7:  # Threshold for similarity
                similar_products.append(product)
    
    return similar_products
def compare_images(img1, img2):
    # Convert images to same size for comparison
    size = (128, 128)
    img1 = img1.resize(size)
    img2 = img2.resize(size)
    
    # Convert to grayscale
    img1 = img1.convert('L')
    img2 = img2.convert('L')
    
    # Convert to array and calculate similarity
    from numpy import array
    pixels1 = array(img1).flatten()
    pixels2 = array(img2).flatten()
    
    from numpy.linalg import norm
    similarity = 1 - (norm(pixels1 - pixels2) / (norm(pixels1) + norm(pixels2)))
    
    return similarity

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
@never_cache
def kids_products(request):
    # Filter products by category 'kids'
    products = Product.objects.filter(category='kids')

    # Get filter parameters
    price = request.GET.get('price')
    colors = request.GET.getlist('color')  # Changed to getlist to handle multiple colors
    sizes = request.GET.getlist('size')    # Changed to getlist to handle multiple sizes
    brand = request.GET.get('brand')
    types = request.GET.getlist('type')    # Changed to getlist to handle multiple types

    # Apply filters
    if price:
        products = products.filter(price__lte=price)
    if colors:
        products = products.filter(color__in=colors)
    if sizes:
        products = products.filter(size__in=sizes)
    if brand:
        products = products.filter(brand__icontains=brand)
    if types:
        products = products.filter(type__in=types)

    # Get unique values for filters
    all_colors = Product.objects.filter(category='kids').values_list('color', flat=True).distinct()
    all_sizes = Product.objects.filter(category='kids').values_list('size', flat=True).distinct()
    all_types = Product.objects.filter(category='kids').values_list('type', flat=True).distinct()

    context = {
        'products': products,
        'all_colors': all_colors,
        'all_sizes': all_sizes,
        'all_types': all_types,
        'selected_colors': colors,
        'selected_sizes': sizes,
        'selected_types': types,
        'selected_price': price,
        'selected_brand': brand,
    }
    return render(request, 'kids_products.html', context)

#womens product
@never_cache
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
@never_cache
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

@never_cache
def add_to_cart(request, product_id):
   if request.method == 'POST':
        size = request.POST.get('size')  
        if not size:
            # Handle missing size, e.g., by returning an error response
            messages.error(request, "Please select a size before adding to the cart.")
            return redirect('product_detail', product_id=product_id)
        if 'user_id' in request.session:
            user_id = request.session['user_id']  # Get the logged-in user ID from session
            user = get_object_or_404(user_registration, id=user_id)
            product = get_object_or_404(Product, id=product_id)

        # Check if the product is in stock
            if product.stock_quantity == 0:
                messages.error(request, f'Sorry, {product.name} is out of stock.')
                return redirect('product_list', category=product.category)  # Redirect with category
            else:
            
                cart_item, created = Cart.objects.get_or_create(user=user, product=product,size=size)
            
                if not created:
                    if cart_item.quantity + 1 > product.stock_quantity:
                        messages.error(request, f'Sorry, only {product.stock_quantity} units of {product.name} are available.')
                    else:
                        cart_item.quantity += 1
                        cart_item.save()
                    messages.success(request, f'{product.name} quantity updated in your cart!')
                else:
                    messages.success(request, f'{product.name} has been added to your cart!')

            return redirect('cart')  # Redirect to cart
        else:
             messages.error(request, "You need to log in to add items to the cart.")
             return redirect('login')

def view_cart(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        
        # Get cart items and saved items for the logged-in user
        cart_items = Cart.objects.filter(user=user, saved_for_later=False)
        saved_items = Cart.objects.filter(user=user, saved_for_later=True)

        # Calculate the subtotal
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        
        # Define additional charges and tax
        shipping_charge = Decimal('0') if subtotal > 0 else Decimal('0')
        platform_fee = Decimal('0')
        tax_rate = Decimal('0')
        tax = tax_rate * subtotal
        
        # Total calculation
        total_amount = subtotal + shipping_charge + platform_fee + tax

        # Prepare context data for the template
        context = {
            'cart_items': cart_items,
            'saved_items': saved_items,
            'subtotal': subtotal,
            'shipping': shipping_charge,
            'platform_fee': platform_fee,
            'tax': tax,
            'total': total_amount,
        }
        return render(request, 'cart.html', context)
    
    else:
        messages.error(request, "You need to log in to view your cart.")
        return redirect('login')
    
    
def remove_from_cart(request, product_id):
    # Get the logged-in user ID from session
    if 'user_id' in request.session:
        user_id = request.session['user_id']
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
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=user)
        quantity = int(request.POST.get('quantity'))

        # Check for stock availability and update if valid
        if quantity > cart_item.product.stock_quantity:
            messages.error(request, f'Sorry, only {cart_item.product.stock_quantity} units of {cart_item.product.name} are available.')
        elif quantity <= 0:
            messages.error(request, "Quantity must be at least 1.")
        else:
            cart_item.quantity = quantity
            cart_item.save()  # Save updated quantity to the database
            messages.success(request, "Cart updated successfully!")
    
    # Redirect back to `view_cart` to refresh the order summary with the updated quantity
    return redirect('cart')


from django.db import transaction

def place_order(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        try:
            # Using transaction to ensure atomic operations
            with transaction.atomic():
                for item in cart_items:
                    product = item.product

                    # Check if the product has enough stock
                    if item.quantity > product.stock_quantity:
                        messages.error(request, f'Sorry, only {product.stock_quantity} units of {product.name} are available.')
                        return redirect('cart')

                    # Reduce the stock quantity
                    product.stock_quantity -= item.quantity
                    product.save()

                # Empty the cart after successful order placement
                cart_items.delete()

                messages.success(request, "Your order has been placed successfully!")
                return redirect('home')
        except Exception as e:
            messages.error(request, "There was an issue placing your order. Please try again.")
            return redirect('cart')
    else:
        messages.error(request, "You need to log in to place an order.")
        return redirect('login')


def billing_details(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        user_profile, created = UserProfile.objects.get_or_create(user=user)  # Get or create the profile

        context = {
            'user_profile': user_profile
        }
        return render(request, 'billing_details.html', context)
    else:
        return redirect('login')

def save_billing_details(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        if request.method == 'POST':
            # Update user details
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.save()

            # Update profile details
            user_profile.phone = request.POST['phone']
            user_profile.pincode = request.POST['pincode']
            user_profile.street = request.POST['street']
            user_profile.house_no = request.POST['house_no']
            user_profile.state = request.POST['state']
            user_profile.district = request.POST.get('district')
            user_profile.save()

            messages.success(request, "Billing details updated successfully!")
            return redirect('billing_details2')  # Replace with the URL of the next page
        else:
            return redirect('billing_details')
    else:
        return redirect('login')

# def billing_details2(request):
#     user_id = request.session.get('user_id')
#     if not user_id:
#         return redirect('login')
    
#     user = get_object_or_404(user_registration, id=user_id)
#     user_profile = user.userprofile
#     cart_items = Cart.objects.filter(user=user, saved_for_later=False)
#     total_price = sum(item.product.price * item.quantity for item in cart_items)
    
#     context = {
#         'user_profile': user_profile,
#         'cart_items': cart_items,
#         'total_price': total_price,
#     }
#     return render(request, 'billing_details2.html', context)



from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, UserProfile, Order, user_registration
from django.core.mail import send_mail

def billing_details2(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(user_registration, id=user_id)
    user_profile = user.userprofile
    cart_items = Cart.objects.filter(user=user, saved_for_later=False)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    # Convert total price to paise (for Razorpay's smallest currency unit)
    total_price_in_paise = int(total_price * 100)

    context = {
        'user_profile': user_profile,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_price_in_paise': total_price_in_paise,  # Add this for Razorpay
    }
    return render(request, 'billing_details2.html', context)




def confirm_order(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        return render(request, 'confirm_order.html', {'payment_method': payment_method})
    return redirect('billing_details2')

def confirm_order_final(request):
    user_id = request.session.get('user_id')
    if not user_id or request.method != 'POST':
        return redirect('login')

    user = get_object_or_404(user_registration, id=user_id)
    confirm_choice = request.POST.get('confirm')
    payment_method = request.POST.get('payment_method')

    if confirm_choice == 'no':
        messages.info(request, "Order was canceled.")
        return redirect('billing_details2')

    cart_items = Cart.objects.filter(user=user, saved_for_later=False)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Create order entries and update stock
    orders = []
    for item in cart_items:
        order = Order.objects.create(
            user=user,
            product=item.product,
            quantity=item.quantity,
            size=item.size,
            total_price=item.product.price * item.quantity,
            payment_method=payment_method,
        )
        orders.append(order)
        item.product.reduce_stock(item.quantity)

    # Clear cart after order placement
    cart_items.delete()

    # Prepare order summary for email
    order_details = "\n".join([
        f"{order.product.name} - Quantity: {order.quantity} - Total: Rs. {order.total_price}"
        for order in orders
    ])
    email_body = (
        f"Hello {user.first_name},\n\nYour order has been confirmed.\n\nOrder Summary:\n"
        f"{order_details}\nTotal: Rs. {total_price}\n\nThank you for shopping with us!"
    )

    # Send confirmation email
    send_mail(
        'Order Confirmation - FootLand',
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )
    
    

    # Redirect based on payment method
    if payment_method == 'cash_on_delivery':
        messages.success(request, "Order confirmed! Confirmation email sent.")
        return redirect('order_summary')
    else:
        return redirect('online_payment')
    
def order_summary(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Fetch the user's orders and profile
    orders = Order.objects.filter(user_id=user_id)
    user_profile = UserProfile.objects.get(user_id=user_id)
    
    return render(request, 'order_summary.html', {'orders': orders, 'user_profile': user_profile})




from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
import qrcode
from django.contrib.staticfiles import finders

def download_order_summary(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    orders = Order.objects.filter(user_id=user_id)
    user_profile = UserProfile.objects.get(user_id=user_id)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=12,
        alignment=1
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#303f9f'),
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#424242')
    )

    # Logo - Find the path of the logo
    logo_path = finders.find('images/logo.jpg')
    if logo_path:
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        elements.append(logo)
    else:
        elements.append(Paragraph("Logo not found", normal_style))  # Fallback if logo is missing

    # Title
    elements.append(Paragraph("FootLand Order Summary", title_style))
    elements.append(Spacer(1, 0.25*inch))

    # Horizontal Line
    d = Drawing(450, 1)
    d.add(Line(0, 0, 450, 0, strokeColor=colors.HexColor('#3f51b5'), strokeWidth=2))
    elements.append(d)
    elements.append(Spacer(1, 0.25*inch))

    # Customer Information
    elements.append(Paragraph("Customer Information", header_style))
    customer_info = [
        f"Name: {user_profile.user.first_name} {user_profile.user.last_name}",
        f"Email: {user_profile.user.email}",
        f"Phone: {user_profile.phone}",
        f"Address: {user_profile.address}, {user_profile.street}, {user_profile.house_no}",
        f"{user_profile.state}, {user_profile.pincode}"
    ]
    for info in customer_info:
        elements.append(Paragraph(info, normal_style))
    elements.append(Spacer(1, 0.25*inch))

    # Order Details
    elements.append(Paragraph("Order Details", header_style))
    data = [["Product", "Quantity", "Size", "Price", "Total"]]
    total_amount = 0
    for order in orders:
        data.append([
            order.product.name,
            str(order.quantity),
            order.size,
            f"Rs. {order.product.price}",
            f"Rs. {order.total_price}"
        ])
        total_amount += order.total_price

    table = Table(data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#424242')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c5cae9'))
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))

    # Total Amount
    elements.append(Paragraph(f"Total Amount: Rs. {total_amount}", header_style))
    elements.append(Spacer(1, 0.25*inch))

    # QR Code
    qr = QrCodeWidget(f"Order Summary for {user_profile.user.email}")
    qr_drawing = Drawing(1*inch, 1*inch, transform=[1*inch/qr.barWidth, 0, 0, 1*inch/qr.barHeight, 0, 0])
    qr_drawing.add(qr)
    elements.append(qr_drawing)

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#757575'),
        alignment=1
    )
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Thank you for shopping with FootLand!", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="FootLand_OrderSummary.pdf")

def email_order_summary(user_profile, orders):
    # Subject and HTML content for the email
    subject = "Your Order Summary - FootLand"
    message = render_to_string('order_summary_email.html', {'user_profile': user_profile, 'orders': orders})

    # Generate PDF attachment
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1a237e'), alignment=1)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#303f9f'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#424242'))

    # Add logo, title, customer info, and order details similar to `download_order_summary`
    elements.append(Paragraph("FootLand Order Summary", title_style))
    elements.append(Spacer(1, 0.25*inch))

    # Customer Information
    elements.append(Paragraph("Customer Information", header_style))
    customer_info = [
        f"Name: {user_profile.user.first_name} {user_profile.user.last_name}",
        f"Email: {user_profile.user.email}",
        f"Phone: {user_profile.phone}",
        f"Address: {user_profile.address}, {user_profile.street}, {user_profile.house_no}",
        f"{user_profile.state}, {user_profile.pincode}"
    ]
    for info in customer_info:
        elements.append(Paragraph(info, normal_style))
    elements.append(Spacer(1, 0.25*inch))

    # Order Details
    elements.append(Paragraph("Order Details", header_style))
    data = [["Product", "Quantity", "Size", "Price", "Total"]]
    total_amount = 0
    for order in orders:
        data.append([
            order.product.name,
            str(order.quantity),
            order.size,
            f"Rs. {order.product.price}",
            f"Rs. {order.total_price}"
        ])
        total_amount += order.total_price

    table = Table(data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#424242')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c5cae9'))
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))

    # Total Amount
    elements.append(Paragraph(f"Total Amount: Rs. {total_amount}", header_style))
    elements.append(Spacer(1, 0.25*inch))

    # Footer
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#757575'), alignment=1)
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Thank you for shopping with FootLand!", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    # Create and send email with PDF attachment
    email = EmailMessage(subject, message, to=[user_profile.user.email])
    email.attach("FootLand_OrderSummary.pdf", buffer.getvalue(), "application/pdf")
    email.send()
    
    
def online_payment(request):
    # Your logic for online payment
    return render(request, 'online_payment.html')
       



def add_to_wishlist(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please log in to add items to your wishlist.")
        return redirect('login')

    user_id = request.session['user_id']
    user = get_object_or_404(user_registration, id=user_id)
    
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
        
        if created:
            messages.success(request, f'{product.name} added to your wishlist.')
        else:
            messages.info(request, f'{product.name} is already in your wishlist.')
        
        return redirect('product_detail', product_id=product_id)

    return redirect('home')  # Redirect to home if not a POST request
def wishlist_view(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please log in to view your wishlist.")
        return redirect('login')  # Redirect to your login page

    user_id = request.session['user_id']
    wishlist_items = Wishlist.objects.filter(user_id=user_id)
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)

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

    # Fetch similar products based on type
    similar_products = Product.objects.filter(
        type=product.type  # Filter by type
    ).exclude(id=product_id)[:5]  # Exclude the current product and limit to 5

    if request.method == 'POST':
        # Handle the adding to cart logic
        user = request.user  # Get the logged-in user
        if user.is_authenticated:  # Check if the user is authenticated
            quantity = request.POST.get('quantity', 1)  # Get the quantity from the form
            cart_item, created = Cart.objects.get_or_create(user=user, product=product)
            cart_item.quantity += int(quantity)  # Increase the quantity
            cart_item.save()  # Save the cart item
            return redirect('cart')  # Redirect to the cart page

    return render(request, 'product_detail.html', {
        'product': product,
        'similar_products': similar_products  # Pass similar products to the template
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    similar_products = Product.objects.filter(type=product.type).exclude(id=product_id)[:4]

    if request.method == 'POST':
        if 'add_to_cart' in request.POST:  # Handle Add to Cart form
            size = request.POST.get('size')
            quantity = int(request.POST.get('quantity', 1))
            user = request.user  # Get the logged-in user

            if user.is_authenticated:
                cart_item, created = Cart.objects.get_or_create(user=user, product=product, size=size)
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, 'Product added to cart successfully!')
                return redirect('cart')
            else:
                messages.error(request, 'You need to be logged in to add products to the cart.')

        elif 'submit_review' in request.POST:  # Handle Review submission form
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, "Your review has been submitted successfully!")
                return redirect('product_detail', product_id=product_id)
            else:
                messages.error(request, "There was an error in your review. Please check the form.")

    else:
        form = ReviewForm()

    return render(request, 'product_detail.html', {
        'product': product,
        'form': form,
        'similar_products': similar_products
    })
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

def save_for_later(request, product_id):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        
        try:
            # Get the first cart item for this product and user
            cart_item = Cart.objects.filter(
                user=user, 
                product_id=product_id, 
                saved_for_later=False
            ).first()
            
            if cart_item:
                cart_item.saved_for_later = True
                cart_item.save()
                messages.success(request, f"{cart_item.product.name} has been saved for later.")
            else:
                messages.error(request, "Item not found in cart.")
                
        except Exception as e:
            messages.error(request, "Error saving item for later.")
            
        return redirect('cart')
    else:
        messages.error(request, "You need to log in to save items for later.")
        return redirect('login')


def move_to_cart(request, product_id):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)
        cart_item = get_object_or_404(Cart, user=user, product_id=product_id)

        cart_item.saved_for_later = False
        cart_item.save()

        messages.success(request, f"{cart_item.product.name} has been moved back to your cart.")
        return redirect('cart')
    else:
        messages.error(request, "You need to log in to move items to the cart.")
        return redirect('login')

def remove_saved_item(request, product_id):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(user_registration, id=user_id)

        # Find the item saved for later in the Cart model
        saved_item = Cart.objects.filter(product_id=product_id, user=user, saved_for_later=True).first()

        if saved_item:
            saved_item.delete()  # Remove the item

        messages.success(request, "Item removed from saved items.")
    else:
        messages.error(request, "You need to log in to remove saved items.")
    
    return redirect('cart')



def my_orders(request):
    user_id = request.session.get('user_id')  # Get the user ID from the session
    if not user_id:
        return redirect('login')  # Redirect to login if the user is not logged in

    user = user_registration.objects.get(id=user_id)  # Get the current user
    orders = Order.objects.filter(user=user).order_by('-order_date')  # Get user's orders, newest first

    return render(request, 'my_orders.html', {'orders': orders})


def view_orders(request):
    # Fetch all orders for the custom orders view
    orders = Order.objects.all()
    context = {
        'orders': orders,
    }
    return render(request, 'view_orders.html', context)

def reject_vendor(request, vendor_id):
    vendor = get_object_or_404(user_registration, id=vendor_id)
    vendor.is_active = False
    vendor.save()
    
    try:
        send_mail(
            'Vendor Application Rejected - Footland',
            f'Dear {vendor.first_name},\n\nWe regret to inform you that your vendor application has been rejected.',
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
        messages.success(request, f'Vendor {vendor.first_name} has been rejected and notified via email.')
    except Exception as e:
        messages.warning(request, f'Vendor rejected but email notification failed: {str(e)}')
    
    return redirect('view_vendors')

from django.db.models import Avg

def vendor_dashboard(request):
    if request.session.get('user_id'):
        vendor = user_registration.objects.get(id=request.session['user_id'])
        vendor_details = VendorDetails.objects.filter(vendor=vendor).first()
        products = Product.objects.filter(vendor=vendor)
        products_count = products.count()
        
        # Get orders count
        orders_count = Order.objects.filter(product__vendor=vendor).count()
        
        # Get average rating safely
        try:
            average_rating = Review.objects.filter(product__in=products).aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or 0.0
            average_rating = round(float(average_rating), 1)
        except Exception as e:
            print(f"Error calculating average rating: {e}")
            average_rating = 0.0

        # Get recent activities (last 5 orders)
        recent_activities = []
        recent_orders = Order.objects.filter(product__vendor=vendor).order_by('-order_date')[:5]
        
        for order in recent_orders:
            activity = {
                'date': order.order_date,
                'description': f"Order #{order.id} - {order.product.name}",
                'status': order.delivery_status
            }
            recent_activities.append(activity)

        context = {
            'vendor': vendor,
            'vendor_details': vendor_details,
            'products_count': products_count,
            'orders_count': orders_count,
            'average_rating': average_rating,
            'recent_activities': recent_activities,
        }
        
        return render(request, 'vendor_dashboard.html', context)
    
    return redirect('login')

def vendor_profile(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user_id = request.session['user_id']
    try:
        vendor = user_registration.objects.get(id=user_id)
        vendor_details = VendorDetails.objects.get(vendor=vendor)
        
        if request.method == 'POST':
            form = VendorDetailsForm(request.POST, request.FILES, instance=vendor_details)
            if form.is_valid():
                vendor_details = form.save(commit=False)
                # Save coordinates and location
                vendor_details.latitude = request.POST.get('latitude')
                vendor_details.longitude = request.POST.get('longitude')
                vendor_details.location = request.POST.get('location')
                vendor_details.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('vendor_profile')
        else:
            form = VendorDetailsForm(instance=vendor_details)
        
        context = {
            'form': form,
            'vendor_details': vendor_details,
            'vendor': vendor
        }
        return render(request, 'vendor_profile.html', context)
    except (user_registration.DoesNotExist, VendorDetails.DoesNotExist):
        messages.error(request, "Vendor profile not found.")
        return redirect('login')

def vendor_change_password(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = user_registration.objects.get(id=request.session['user_id'])
        
        if not check_password(current_password, user.password):
            messages.error(request, "Current password is incorrect.")
            return redirect('vendor_change_password')
            
        if new_password != confirm_password:
            messages.error(request, "New passwords don't match.")
            return redirect('vendor_change_password')
            
        user.password = make_password(new_password)
        user.save()
        messages.success(request, "Password changed successfully!")
        return redirect('vendor_dashboard')
        
    return render(request, 'vendor_change_password.html')

def vendor_add_product(request):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = user_registration.objects.get(id=request.session['user_id'])
            product.save()
            messages.success(request, "Product added successfully!")
            return redirect('vendor_view_products')
    else:
        form = ProductForm()
    
    return render(request, 'vendor_add_product.html', {'form': form})

def vendor_view_products(request):
    vendor = user_registration.objects.get(id=request.session['user_id'])
    products = Product.objects.filter(vendor=vendor)
    return render(request, 'vendor_view_products.html', {'products': products})

def vendor_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor_id=request.session['user_id'])
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()  # Save the product instance
            product.check_stock_alert()  # Check stock after editing
            messages.success(request, "Product updated successfully!")
            return redirect('vendor_view_products')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'vendor_edit_product.html', {'form': form, 'product': product})

def vendor_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor_id=request.session['user_id'])
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('vendor_view_products')

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        try:
            # Create the model
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Generate content using the user message
            response = model.generate_content(user_message)

            # Extract the AI response   
            ai_message = response.text

            # Log the AI response for debugging
            logger.info(f"Gemini API response: {ai_message}")

            return JsonResponse({'response': ai_message})

        except Exception as e:
            logger.error(f"Error fetching response from Gemini API: {str(e)}")
            return JsonResponse({'error': 'Failed to get response from AI'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


from django.db.models import Count, Sum, Avg, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal

def vendor_performance_analytics(request):
    if 'user_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    try:
        vendor = get_object_or_404(user_registration, id=request.session['user_id'])
        
        # Get vendor's products first
        vendor_products = Product.objects.filter(vendor=vendor)
        
        # Get all orders for vendor's products
        vendor_orders = Order.objects.filter(product__in=vendor_products)
        
        # Calculate total revenue from all time
        total_revenue = vendor_orders.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Get best selling products using product__in
        best_selling = Order.objects.filter(
            product__in=vendor_products
        ).values(
            'product__name'
        ).annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total_price')
        ).order_by('-total_sales')[:5]

        # Weekly revenue calculation
        today = timezone.now()
        weekly_revenue = []
        
        for i in range(4):
            start_date = today - timedelta(days=(i+1)*7)
            end_date = today - timedelta(days=i*7)
            
            week_data = vendor_orders.filter(
                order_date__range=[start_date, end_date]
            ).aggregate(
                revenue=Sum('total_price'),
                orders=Count('id')
            )
            
            weekly_revenue.append({
                'week': f'Week {4-i}',
                'revenue': week_data['revenue'] or 0,
                'orders': week_data['orders'] or 0
            })

        # Customer metrics using product__in
        customer_stats = {
            'total_customers': vendor_orders.values('user').distinct().count(),
            'repeat_customers': vendor_orders.values('user').annotate(
                order_count=Count('id')
            ).filter(order_count__gt=1).count(),
            'avg_order_value': vendor_orders.aggregate(
                avg=Avg('total_price')
            )['avg'] or 0
        }

        # Monthly revenue using product__in
        monthly_revenue = vendor_orders.filter(
            order_date__month=today.month,
            order_date__year=today.year
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        # Debug prints
        print("Debug Info:")
        print(f"Vendor ID: {vendor.id}")
        print(f"Total Products: {vendor_products.count()}")
        print(f"Total Orders: {vendor_orders.count()}")
        print(f"Total Revenue: {total_revenue}")
        print(f"Monthly Revenue: {monthly_revenue}")
        print(f"Customer Stats: {customer_stats}")

        context = {
            'vendor': vendor,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'best_selling': best_selling,
            'weekly_revenue': weekly_revenue,
            'customer_stats': customer_stats,
            'low_stock_products': vendor_products.filter(stock_quantity__lt=5),
            'total_orders': vendor_orders.count()
        }
        
        return render(request, 'vendor_performance_analytics.html', context)
    
    except Exception as e:
        print(f"Error in vendor_performance_analytics: {str(e)}")
        messages.error(request, "An error occurred while fetching analytics data.")
        return redirect('vendor_dashboard')

def generate_password():
    # Generate a random password
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for i in range(12))
    # Ensure password contains at least one of each required type
    password = (random.choice(string.ascii_uppercase) +
               random.choice(string.ascii_lowercase) +
               random.choice(string.digits) +
               random.choice("!@#$%^&*") +
               password)
    return password


def add_delivery_boy(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        # Validation
        if not all([first_name, last_name, email, phone]):
            messages.error(request, 'All fields are required!')
            return render(request, 'add_delivery_boy.html')
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format!')
            return render(request, 'add_delivery_boy.html')
            
        # Improved phone number validation
        # Remove any spaces or special characters from phone number
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check if phone number is valid (10 digits)
        if len(phone) != 10:
            messages.error(request, 'Phone number must be 10 digits!')
            return render(request, 'add_delivery_boy.html')
        
        # Check if email already exists
        if user_registration.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'add_delivery_boy.html')
        
        # Generate a random password
        password = generate_password()
        
        try:
            # Create new delivery boy user in user_registration with is_active=True
            new_user = user_registration(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(password),
                user_type='delivery_boy',
                is_active=True  # Set this to True
            )
            new_user.save()
            
            # Create delivery boy record with is_active=True
            delivery_boy = DeliveryBoy(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                is_active=True  # Make sure this matches user_registration
            )
            delivery_boy.save()
            
            # Send email with credentials
            subject = 'Welcome to Footland - Delivery Partner'
            message = f"""
            Hello {first_name},

            Welcome to Footland! You have been registered as a delivery partner.

            Your login credentials are:
            Email: {email}
            Password: {password}

            Please login using these credentials at: http://127.0.0.1:8000/login

            For security reasons, we recommend changing your password after your first login.

            Best regards,
            Footland Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Delivery boy registered successfully! Login credentials have been sent to their email.')
            return redirect('view_delivery_boys')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'add_delivery_boy.html')
    
    return render(request, 'add_delivery_boy.html')


def view_delivery_boys(request):
    delivery_boys = DeliveryBoy.objects.all().order_by('-created_at')
    return render(request, 'view_delivery_boys.html', {'delivery_boys': delivery_boys})


def toggle_delivery_boy_status(request, delivery_boy_id):
    if request.method == 'POST':
        try:
            # Get both delivery boy and user records
            delivery_boy = DeliveryBoy.objects.get(id=delivery_boy_id)
            user = user_registration.objects.get(email=delivery_boy.email)
            
            # Toggle status
            delivery_boy.is_active = not delivery_boy.is_active
            delivery_boy.save()
            
            # Update user_registration status as well
            user.is_active = delivery_boy.is_active
            user.save()
            
            status = "unblocked" if delivery_boy.is_active else "blocked"
            messages.success(request, f'Delivery boy has been {status} successfully.')
            
            # Send email notification
            subject = f'Your Footland Account Status Update'
            message = f"""
            Hello {delivery_boy.first_name},

            Your Footland delivery partner account has been {status}.
            {"You can now login to your account." if delivery_boy.is_active else "Your account access has been temporarily suspended."}

            If you have any questions, please contact the administrator.

            Best regards,
            Footland Team
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [delivery_boy.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'Status updated but email notification failed: {str(e)}')
                
        except DeliveryBoy.DoesNotExist:
            messages.error(request, 'Delivery boy not found.')
        except user_registration.DoesNotExist:
            messages.error(request, 'User registration not found.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('view_delivery_boys')

def delivery_boy_profile_view(request):
    try:
        # Get the delivery boy using email from session
        delivery_boy = DeliveryBoy.objects.get(email=request.session.get('email'))
        profile, created = DeliveryBoyProfile.objects.get_or_create(delivery_boy=delivery_boy)
        
        # Add print statements for debugging
        print(f"Delivery Boy: {delivery_boy.first_name} {delivery_boy.last_name}")
        print(f"Email: {delivery_boy.email}")
        print(f"Phone: {delivery_boy.phone_number}")
        
        context = {
            'delivery_boy': delivery_boy,
            'profile': profile
        }
        return render(request, 'delivery_boy_profile.html', context)
    except DeliveryBoy.DoesNotExist:
        messages.error(request, 'Profile not found')
        return redirect('login')

def delivery_boy_profile_edit(request):
    try:
        delivery_boy = DeliveryBoy.objects.get(email=request.session.get('email'))
        profile, created = DeliveryBoyProfile.objects.get_or_create(delivery_boy=delivery_boy)
        
        if request.method == 'POST':
            # Update delivery boy details
            delivery_boy.first_name = request.POST.get('first_name')
            delivery_boy.last_name = request.POST.get('last_name')
            delivery_boy.phone_number = request.POST.get('phone_number')
            delivery_boy.save()
            
            # Update profile details
            profile.address = request.POST.get('address')
            profile.postal_code = request.POST.get('postal_code')
            profile.district = request.POST.get('district')
            
            profile.nationality = request.POST.get('nationality')
            
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            
            profile.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('delivery_boy_profile')
        
        context = {
            'profile': profile,
            'delivery_boy': delivery_boy
        }
        return render(request, 'delivery_boy_profile_edit.html', context)
    except DeliveryBoy.DoesNotExist:
        messages.error(request, 'Profile not found')
        return redirect('login')

def delivery_boy_change_password(request):
    try:
        # Get the delivery boy instance
        delivery_boy = DeliveryBoy.objects.get(email=request.session.get('email'))
        
        # Get the user_registration instance associated with the delivery boy
        user = user_registration.objects.get(email=delivery_boy.email)
        
        profile = DeliveryBoyProfile.objects.get(delivery_boy=delivery_boy)

        if request.method == 'POST':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Check the password against the user_registration model
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect')
                return redirect('delivery_boy_change_password')
                
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match')
                return redirect('delivery_boy_change_password')
                
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password changed successfully')
            return redirect('delivery_boy_profile')

        context = {
            'profile': profile,
            'delivery_boy': delivery_boy
        }
        return render(request, 'delivery_boy_change_password.html', context)
    
    except DeliveryBoy.DoesNotExist:
        messages.error(request, 'Delivery Boy not found')
        return redirect('login')
    except DeliveryBoyProfile.DoesNotExist:
        messages.error(request, 'Profile not found')
        return redirect('login')
    except user_registration.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    
from datetime import datetime, timedelta
from django.db.models import Count

def delivery_history(request):
    if 'email' not in request.session:
        return redirect('login')
    
    delivery_boy = get_object_or_404(DeliveryBoy, email=request.session['email'])
    
    # Get filter parameters from request
    date_filter = request.GET.get('date_filter', 'all')
    status_filter = request.GET.get('status_filter', 'all')
    
    # Base queryset
    deliveries = DeliveryAssignment.objects.filter(delivery_boy=delivery_boy)
    
    # Apply date filter
    if date_filter == 'today':
        deliveries = deliveries.filter(assigned_date=date.today())
    elif date_filter == 'week':
        week_ago = date.today() - timedelta(days=7)
        deliveries = deliveries.filter(assigned_date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = date.today() - timedelta(days=30)
        deliveries = deliveries.filter(assigned_date__gte=month_ago)
    
    # Apply status filter
    if status_filter != 'all':
        deliveries = deliveries.filter(delivery_status=status_filter)
    
    # Order by most recent first
    deliveries = deliveries.order_by('-assigned_date', '-updated_at')
    
    # Get delivery statistics
    stats = {
        'total_deliveries': deliveries.count(),
        'successful_deliveries': deliveries.filter(delivery_status='delivered').count(),
        'failed_deliveries': deliveries.filter(delivery_status='failed').count(),
        'success_rate': round(
            (deliveries.filter(delivery_status='delivered').count() / deliveries.count() * 100)
            if deliveries.count() > 0 else 0,
            1
        )
    }
    
    # Pagination
    paginator = Paginator(deliveries, 10)  # Show 10 deliveries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'delivery_boy': delivery_boy,
        'page_obj': page_obj,
        'stats': stats,
        'date_filter': date_filter,
        'status_filter': status_filter
    }
    
    return render(request, 'delivery_history.html', context)
    
  
    
from django.utils import timezone

def scan_delivery_qr(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            assignment = DeliveryAssignment.objects.get(
                order=order,
                delivery_status='out_for_delivery'
            )
            
            assignment.delivery_status = 'delivered'
            assignment.save()
            
            order.delivery_status = 'Delivered'
            order.save()
            
            return JsonResponse({'status': 'success'})
        except (Order.DoesNotExist, DeliveryAssignment.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid order or delivery'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def qr_scanner(request):
    if 'email' not in request.session:
        return redirect('login')
    
    delivery_boy = get_object_or_404(DeliveryBoy, email=request.session['email'])
    
    return render(request, 'qr_scanner.html', {'delivery_boy': delivery_boy})

def order_detail(request, order_id):
    if 'user_id' not in request.session:
        return redirect('login')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Ensure the order belongs to the logged-in user
    if order.user.id != request.session['user_id']:
        messages.error(request, "You don't have permission to view this order")
        return redirect('my_orders')
    
    # Get delivery assignment if exists
    try:
        delivery_assignment = DeliveryAssignment.objects.get(order=order)
    except DeliveryAssignment.DoesNotExist:
        delivery_assignment = None
    
    # Generate QR code if not exists
    if not order.qr_code:
        order.generate_qr_code()
        order.save()
    
    context = {
        'order': order,
        'delivery_assignment': delivery_assignment,
    }
    
    return render(request, 'order_detail.html', context)

def track_order(request, order_id):
    if 'user_id' not in request.session:
        return redirect('login')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Ensure the order belongs to the logged-in user
    if order.user.id != request.session['user_id']:
        messages.error(request, "You don't have permission to view this order")
        return redirect('my_orders')
    
    # Get delivery assignment if exists
    try:
        delivery_assignment = DeliveryAssignment.objects.get(order=order)
    except DeliveryAssignment.DoesNotExist:
        delivery_assignment = None
    
    # Generate QR code if not exists
    if not order.qr_code:
        order.generate_qr_code()
        order.save()
    
    context = {
        'order': order,
        'delivery_assignment': delivery_assignment,
    }
    
    return render(request, 'track_order.html', context)





import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Initialize label encoders for categorical variables
footwear_encoder = LabelEncoder()
activity_encoder = LabelEncoder()
surface_encoder = LabelEncoder()
material_encoder = LabelEncoder()
usage_frequency_encoder = LabelEncoder()
temperature_encoder = LabelEncoder()
condition_encoder = LabelEncoder()

# At the top with other initializations, let's pre-fit the encoders with all possible values
footwear_encoder.fit(['casual_shoes', 'sports_shoes', 'formal_shoes', 'work_boots', 'safety_shoes'])
activity_encoder.fit(['walking', 'running', 'standing', 'climbing', 'mixed'])
usage_frequency_encoder.fit(['daily', 'weekly', 'occasional', 'rare'])
temperature_encoder.fit(['cold', 'mild', 'warm', 'hot'])
surface_encoder.fit(['ceramic_tile', 'polished_marble', 'vinyl', 'hardwood', 'concrete', 
                    'asphalt', 'grass', 'gravel', 'wet_tile', 'inclined', 'metal_grating', 'pool_deck'])
condition_encoder.fit(['dry', 'wet', 'oily', 'dusty', 'frozen'])

# Update the material encoder initialization and fitting
material_encoder.fit([
    'Natural rubber', 'Heavy-duty rubber', 'Non-marking rubber',
    'TPR', 'PVC', 'Nitrile rubber', 'SBR rubber', 'EVA',
    'Polyurethane', 'Neoprene', 'Vibram', 'Cork'
])

# Expand the training data
sample_training_data = [
    # Format: age, weight, shoe_size, prev_incidents, footwear_type, activity, usage_freq, temp, surface_type, surface_condition, material
    [25, 70, 9, 0, 'casual_shoes', 'walking', 'daily', 'mild', 'ceramic_tile', 'dry', 'Natural rubber'],
    [30, 65, 8, 1, 'sports_shoes', 'running', 'weekly', 'warm', 'concrete', 'wet', 'Heavy-duty rubber'],
    [45, 80, 10, 0, 'formal_shoes', 'standing', 'daily', 'mild', 'polished_marble', 'dry', 'Non-marking rubber'],
    [28, 75, 8.5, 0, 'casual_shoes', 'walking', 'daily', 'mild', 'ceramic_tile', 'wet', 'TPR'],
    [35, 82, 11, 2, 'work_boots', 'standing', 'daily', 'hot', 'concrete', 'oily', 'Nitrile rubber'],
    [42, 68, 7, 1, 'sports_shoes', 'running', 'weekly', 'cold', 'asphalt', 'wet', 'SBR rubber'],
    [29, 63, 6.5, 0, 'safety_shoes', 'standing', 'daily', 'warm', 'metal_grating', 'oily', 'Vibram'],
    [33, 77, 9.5, 1, 'casual_shoes', 'walking', 'occasional', 'mild', 'vinyl', 'wet', 'PVC'],
    [38, 85, 10.5, 2, 'work_boots', 'standing', 'daily', 'hot', 'metal_grating', 'oily', 'Nitrile rubber'],
    [27, 72, 8, 0, 'sports_shoes', 'running', 'weekly', 'mild', 'hardwood', 'dry', 'EVA'],
    [31, 69, 7.5, 1, 'casual_shoes', 'walking', 'daily', 'cold', 'polished_marble', 'wet', 'Natural rubber'],
    [40, 78, 9, 2, 'safety_shoes', 'standing', 'daily', 'warm', 'concrete', 'oily', 'Heavy-duty rubber'],
    [36, 73, 8.5, 0, 'formal_shoes', 'walking', 'occasional', 'mild', 'ceramic_tile', 'dry', 'Non-marking rubber'],
    [34, 81, 10, 1, 'work_boots', 'standing', 'daily', 'hot', 'asphalt', 'oily', 'SBR rubber'],
    [32, 67, 7, 0, 'sports_shoes', 'running', 'weekly', 'warm', 'grass', 'wet', 'TPR'],
    [39, 76, 9, 2, 'safety_shoes', 'standing', 'daily', 'mild', 'metal_grating', 'oily', 'Nitrile rubber'],
    [28, 70, 8, 0, 'casual_shoes', 'walking', 'daily', 'cold', 'polished_marble', 'wet', 'Natural rubber'],
    [37, 83, 11, 1, 'work_boots', 'standing', 'daily', 'hot', 'concrete', 'oily', 'Heavy-duty rubber'],
    [41, 74, 8.5, 0, 'formal_shoes', 'walking', 'occasional', 'mild', 'vinyl', 'dry', 'Non-marking rubber'],
    [30, 79, 9.5, 2, 'safety_shoes', 'standing', 'daily', 'warm', 'metal_grating', 'oily', 'Vibram'],
    [29, 71, 8.5, 0, 'casual_shoes', 'walking', 'daily', 'mild', 'hardwood', 'dry', 'Natural rubber'],
    [31, 68, 7.5, 1, 'casual_shoes', 'walking', 'daily', 'warm', 'concrete', 'dry', 'Heavy-duty rubber'],
    [27, 65, 8.0, 0, 'sports_shoes', 'running', 'weekly', 'mild', 'asphalt', 'dry', 'SBR rubber'],
    [33, 70, 9.0, 1, 'sports_shoes', 'running', 'daily', 'warm', 'grass', 'dry', 'TPR'],
    [35, 75, 8.5, 0, 'safety_shoes', 'standing', 'daily', 'mild', 'concrete', 'dry', 'Nitrile rubber'],
    [40, 80, 10.0, 1, 'work_boots', 'standing', 'daily', 'warm', 'metal_grating', 'oily', 'Heavy-duty rubber'],
    [28, 70, 8.5, 0, 'sports_shoes', 'climbing', 'weekly', 'mild', 'metal_grating', 'dry', 'Vibram'],
    [32, 75, 9.0, 1, 'work_boots', 'climbing', 'occasional', 'warm', 'concrete', 'dry', 'Heavy-duty rubber'],
    [30, 72, 8.0, 0, 'sports_shoes', 'mixed', 'daily', 'mild', 'vinyl', 'dry', 'TPR'],
    [34, 77, 9.5, 1, 'casual_shoes', 'mixed', 'weekly', 'warm', 'ceramic_tile', 'dry', 'Natural rubber'],
    [31, 72, 8.5, 0, 'work_boots', 'walking', 'daily', 'mild', 'concrete', 'dusty', 'Heavy-duty rubber'],
    [29, 68, 7.5, 1, 'safety_shoes', 'standing', 'daily', 'warm', 'metal_grating', 'dusty', 'Nitrile rubber'],
    [33, 75, 9.0, 0, 'work_boots', 'mixed', 'daily', 'hot', 'asphalt', 'dusty', 'SBR rubber'],
    [35, 70, 8.0, 1, 'safety_shoes', 'standing', 'daily', 'warm', 'concrete', 'dusty', 'Heavy-duty rubber'],
    [28, 73, 8.5, 0, 'sports_shoes', 'running', 'weekly', 'mild', 'gravel', 'dusty', 'Vibram'],
    [32, 77, 9.5, 1, 'work_boots', 'climbing', 'occasional', 'warm', 'metal_grating', 'dusty', 'Heavy-duty rubber'],
    [30, 69, 8.0, 0, 'safety_shoes', 'standing', 'daily', 'hot', 'concrete', 'dusty', 'Nitrile rubber'],
    [34, 74, 9.0, 1, 'work_boots', 'mixed', 'daily', 'warm', 'asphalt', 'dusty', 'SBR rubber'],
    [36, 71, 8.5, 0, 'sports_shoes', 'running', 'weekly', 'mild', 'gravel', 'dusty', 'TPR'],
    [31, 76, 9.5, 1, 'safety_shoes', 'standing', 'daily', 'hot', 'metal_grating', 'dusty', 'Nitrile rubber'],
    [27, 70, 8.0, 0, 'work_boots', 'walking', 'daily', 'cold', 'concrete', 'frozen', 'Heavy-duty rubber'],
    [33, 75, 9.5, 1, 'safety_shoes', 'standing', 'daily', 'cold', 'metal_grating', 'frozen', 'Nitrile rubber'],
    [29, 72, 8.5, 0, 'sports_shoes', 'running', 'weekly', 'cold', 'asphalt', 'frozen', 'SBR rubber'],
    [35, 78, 10.0, 1, 'work_boots', 'mixed', 'daily', 'cold', 'concrete', 'frozen', 'Heavy-duty rubber'],
    [31, 73, 9.0, 0, 'safety_shoes', 'standing', 'daily', 'cold', 'metal_grating', 'frozen', 'Vibram'],
    [28, 71, 8.5, 1, 'sports_shoes', 'climbing', 'occasional', 'cold', 'concrete', 'frozen', 'Heavy-duty rubber'],
    [34, 76, 9.5, 0, 'work_boots', 'mixed', 'daily', 'cold', 'asphalt', 'frozen', 'SBR rubber'],
    [30, 74, 9.0, 1, 'safety_shoes', 'standing', 'daily', 'cold', 'metal_grating', 'frozen', 'Nitrile rubber'],
    [32, 77, 9.5, 0, 'sports_shoes', 'running', 'weekly', 'cold', 'concrete', 'frozen', 'TPR'],
    [36, 79, 10.0, 1, 'work_boots', 'climbing', 'occasional', 'cold', 'metal_grating', 'frozen', 'Vibram'],
    # Pool deck entries
    # Format: age, weight, shoe_size, prev_incidents, footwear_type, activity, usage_freq, temp, surface_type, surface_condition, material
    
    # Pool deck - wet condition (most common)
    [28, 70, 8.5, 0, 'sports_shoes', 'walking', 'daily', 'warm', 'pool_deck', 'wet', 'Neoprene'],
    [31, 75, 9.0, 1, 'casual_shoes', 'walking', 'weekly', 'hot', 'pool_deck', 'wet', 'TPR'],
    [29, 68, 7.5, 0, 'sports_shoes', 'standing', 'daily', 'warm', 'pool_deck', 'wet', 'Non-marking rubber'],
    [33, 72, 8.0, 1, 'casual_shoes', 'mixed', 'weekly', 'hot', 'pool_deck', 'wet', 'PVC'],
    [35, 77, 9.5, 0, 'sports_shoes', 'walking', 'daily', 'warm', 'pool_deck', 'wet', 'Neoprene'],

    # Pool deck - dry condition
    [30, 73, 8.5, 0, 'casual_shoes', 'walking', 'daily', 'warm', 'pool_deck', 'dry', 'Non-marking rubber'],
    [32, 76, 9.0, 1, 'sports_shoes', 'standing', 'weekly', 'hot', 'pool_deck', 'dry', 'TPR'],
    [34, 71, 8.0, 0, 'casual_shoes', 'mixed', 'daily', 'warm', 'pool_deck', 'dry', 'PVC'],
    [27, 69, 7.5, 1, 'sports_shoes', 'walking', 'weekly', 'hot', 'pool_deck', 'dry', 'Non-marking rubber'],
    [36, 78, 9.5, 0, 'casual_shoes', 'standing', 'daily', 'warm', 'pool_deck', 'dry', 'Neoprene'],

    # Wet tile specific entries (different from regular ceramic tile)
    # Wet tile - wet condition
    [29, 71, 8.0, 1, 'casual_shoes', 'walking', 'daily', 'mild', 'wet_tile', 'wet', 'Non-marking rubber'],
    [31, 74, 8.5, 0, 'sports_shoes', 'standing', 'weekly', 'warm', 'wet_tile', 'wet', 'Natural rubber'],
    [33, 77, 9.0, 1, 'work_boots', 'mixed', 'daily', 'mild', 'wet_tile', 'wet', 'Heavy-duty rubber'],
    [28, 70, 7.5, 0, 'safety_shoes', 'standing', 'daily', 'warm', 'wet_tile', 'wet', 'Nitrile rubber'],
    [35, 73, 8.5, 1, 'casual_shoes', 'walking', 'weekly', 'mild', 'wet_tile', 'wet', 'TPR'],

    # Wet tile - dry condition
    [30, 72, 8.5, 0, 'casual_shoes', 'walking', 'daily', 'mild', 'wet_tile', 'dry', 'Non-marking rubber'],
    [32, 75, 9.0, 1, 'sports_shoes', 'standing', 'weekly', 'warm', 'wet_tile', 'dry', 'Natural rubber'],
    [34, 78, 9.5, 0, 'work_boots', 'mixed', 'daily', 'mild', 'wet_tile', 'dry', 'Heavy-duty rubber'],
    [27, 69, 7.5, 1, 'safety_shoes', 'standing', 'daily', 'warm', 'wet_tile', 'dry', 'Nitrile rubber'],
    [36, 74, 8.5, 0, 'casual_shoes', 'walking', 'weekly', 'mild', 'wet_tile', 'dry', 'TPR'],

    # Wet tile - oily condition
    [31, 73, 8.5, 1, 'safety_shoes', 'standing', 'daily', 'mild', 'wet_tile', 'oily', 'Nitrile rubber'],
    [29, 71, 8.0, 0, 'work_boots', 'mixed', 'daily', 'warm', 'wet_tile', 'oily', 'Heavy-duty rubber'],
    [33, 76, 9.0, 1, 'safety_shoes', 'standing', 'weekly', 'mild', 'wet_tile', 'oily', 'SBR rubber'],
    [35, 72, 8.5, 0, 'work_boots', 'mixed', 'daily', 'warm', 'wet_tile', 'oily', 'Nitrile rubber'],
    [28, 70, 7.5, 1, 'safety_shoes', 'standing', 'weekly', 'mild', 'wet_tile', 'oily', 'Heavy-duty rubber']
]

# Add these entries to sample_training_data
sample_training_data.extend([
    # Inclined surfaces with various conditions
    # Format: age, weight, shoe_size, prev_incidents, footwear_type, activity, usage_freq, temp, surface_type, surface_condition, material

    # Inclined - wet condition
    [29, 70, 8.5, 1, 'safety_shoes', 'climbing', 'daily', 'mild', 'inclined', 'wet', 'Vibram'],
    [31, 75, 9.0, 0, 'work_boots', 'mixed', 'daily', 'warm', 'inclined', 'wet', 'Heavy-duty rubber'],
    [33, 72, 8.0, 1, 'sports_shoes', 'climbing', 'weekly', 'mild', 'inclined', 'wet', 'SBR rubber'],
    [28, 68, 7.5, 0, 'safety_shoes', 'climbing', 'daily', 'warm', 'inclined', 'wet', 'Nitrile rubber'],
    [35, 77, 9.5, 1, 'work_boots', 'mixed', 'daily', 'mild', 'inclined', 'wet', 'Heavy-duty rubber'],

    # Inclined - oily condition
    [30, 73, 8.5, 1, 'safety_shoes', 'climbing', 'daily', 'mild', 'inclined', 'oily', 'Nitrile rubber'],
    [32, 76, 9.0, 0, 'work_boots', 'mixed', 'daily', 'warm', 'inclined', 'oily', 'Heavy-duty rubber'],
    [34, 71, 8.0, 1, 'safety_shoes', 'climbing', 'daily', 'mild', 'inclined', 'oily', 'SBR rubber'],
    [27, 69, 7.5, 0, 'work_boots', 'mixed', 'daily', 'warm', 'inclined', 'oily', 'Nitrile rubber'],
    [36, 78, 9.5, 1, 'safety_shoes', 'climbing', 'daily', 'mild', 'inclined', 'oily', 'Heavy-duty rubber'],

    # Inclined - dusty condition
    [31, 74, 8.5, 0, 'work_boots', 'climbing', 'daily', 'warm', 'inclined', 'dusty', 'Vibram'],
    [29, 70, 8.0, 1, 'safety_shoes', 'mixed', 'daily', 'mild', 'inclined', 'dusty', 'Heavy-duty rubber'],
    [33, 75, 9.0, 0, 'work_boots', 'climbing', 'daily', 'warm', 'inclined', 'dusty', 'SBR rubber'],
    [35, 72, 8.5, 1, 'safety_shoes', 'mixed', 'daily', 'mild', 'inclined', 'dusty', 'Nitrile rubber'],
    [28, 69, 7.5, 0, 'work_boots', 'climbing', 'daily', 'warm', 'inclined', 'dusty', 'Heavy-duty rubber'],

    # Inclined - frozen condition
    [32, 73, 8.5, 1, 'safety_shoes', 'climbing', 'daily', 'cold', 'inclined', 'frozen', 'Vibram'],
    [34, 77, 9.0, 0, 'work_boots', 'mixed', 'daily', 'cold', 'inclined', 'frozen', 'Heavy-duty rubber'],
    [30, 71, 8.0, 1, 'safety_shoes', 'climbing', 'daily', 'cold', 'inclined', 'frozen', 'Nitrile rubber'],
    [36, 76, 9.5, 0, 'work_boots', 'mixed', 'daily', 'cold', 'inclined', 'frozen', 'SBR rubber'],
    [28, 70, 7.5, 1, 'safety_shoes', 'climbing', 'daily', 'cold', 'inclined', 'frozen', 'Heavy-duty rubber']
])

def train_model():
    # Convert training data to numpy arrays
    X = np.array([[x[0], x[1], x[2], x[3]] for x in sample_training_data])  # Numerical features
    categorical_features = np.array([[x[4], x[5], x[6], x[7], x[8], x[9]] for x in sample_training_data])
    y = np.array([x[10] for x in sample_training_data])

    # Encode categorical variables
    X_cat_encoded = np.column_stack([
        footwear_encoder.fit_transform(categorical_features[:, 0]),
        activity_encoder.fit_transform(categorical_features[:, 1]),
        usage_frequency_encoder.fit_transform(categorical_features[:, 2]),
        temperature_encoder.fit_transform(categorical_features[:, 3]),
        surface_encoder.fit_transform(categorical_features[:, 4]),
        condition_encoder.fit_transform(categorical_features[:, 5])
    ])

    # Combine numerical and encoded categorical features
    X_combined = np.column_stack([X, X_cat_encoded])
    
    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_combined, material_encoder.fit_transform(y))
    
    return model

def get_recommendations(age, weight, shoe_size, prev_incidents, footwear_type, activity, 
                       usage_freq, temperature, surfaces, surface_conditions):
    try:
        print("Starting get_recommendations with inputs:", {
            'age': age, 'weight': weight, 'shoe_size': shoe_size,
            'prev_incidents': prev_incidents, 'footwear_type': footwear_type,
            'activity': activity, 'usage_freq': usage_freq,
            'temperature': temperature, 'surfaces': surfaces,
            'surface_conditions': surface_conditions
        })

        # Force retrain the model every time (for development)
        model = train_model()
        
        recommendations = {}
        activities = ['walking', 'running', 'standing', 'climbing', 'mixed']
        prev_incidents = int(prev_incidents)
        numerical_features = np.array([age, weight, shoe_size, prev_incidents])
        
        for surface in surfaces:
            for condition in surface_conditions:
                surface_predictions = {}
                
                # Get predictions for each activity type
                for act in activities:
                    try:
                        categorical_features = np.array([
                            footwear_encoder.transform([footwear_type])[0],
                            activity_encoder.transform([act])[0],
                            usage_frequency_encoder.transform([usage_freq])[0],
                            temperature_encoder.transform([temperature])[0],
                            surface_encoder.transform([surface])[0],
                            condition_encoder.transform([condition])[0]
                        ])
                        
                        X = np.concatenate([numerical_features, categorical_features]).reshape(1, -1)
                        probabilities = model.predict_proba(X)[0]
                        top_3_indices = np.argsort(probabilities)[-3:][::-1]
                        recommended_materials = material_encoder.inverse_transform(top_3_indices)
                        probs = probabilities[top_3_indices]
                        descriptions = get_material_descriptions(recommended_materials.tolist())
                        
                        # Format the materials info
                        materials_info = []
                        for mat, prob in zip(recommended_materials, probs):
                            materials_info.append({
                                'name': mat,
                                'percentage': round(prob * 100, 1),
                                'description': descriptions[mat]
                            })
                        
                        surface_predictions[act] = {
                            'materials_info': materials_info
                        }
                    except Exception as e:
                        print(f"Error processing activity {act}: {str(e)}")
                        continue

                surface_display = surface.replace('_', ' ').title()
                surface_key = f"{surface_display}_{condition}"
                recommendations[surface_key] = {
                    'predictions': surface_predictions,
                    'condition': condition
                }
        
        return recommendations
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return {'error': str(e)}

def get_material_descriptions(materials):
    descriptions = {
        'Natural rubber': 'Excellent grip in wet conditions, good durability, and moderate heat resistance.',
        'Heavy-duty rubber': 'Superior durability and excellent slip resistance, ideal for industrial settings.',
        'Non-marking rubber': 'Good grip without leaving marks, perfect for indoor surfaces.',
        'TPR': 'Thermoplastic rubber offering good flexibility and moderate slip resistance.',
        'PVC': 'Durable and chemical resistant, moderate slip resistance.',
        'Nitrile rubber': 'Outstanding oil and chemical resistance, excellent for industrial use.',
        'SBR rubber': 'Good abrasion resistance and grip, economical choice.',
        'EVA': 'Lightweight and cushioning, moderate slip resistance.',
        'Polyurethane': 'Excellent wear resistance and good grip, versatile material.',
        'Neoprene': 'Good chemical resistance and moderate grip, water-friendly.',
        'Vibram': 'Premium grip and durability, excellent for outdoor use.',
        'Cork': 'Natural material with good grip when dry, eco-friendly option.'
    }
    return {material: descriptions.get(material, 'Properties not specified') for material in materials}

def recommend(request):
    if request.method == 'POST':
        try:
            # Get form data with default values and type conversion
            age = int(request.POST.get('age', 0))
            weight = float(request.POST.get('weight', 0))
            shoe_size = float(request.POST.get('shoeSize', 0))
            prev_incidents = request.POST.get('previousIncidents')
            footwear_type = request.POST.get('footwearType')
            activity = request.POST.get('activity')
            usage_freq = request.POST.get('usageFrequency')
            temperature = request.POST.get('temperature')
            surfaces = request.POST.getlist('surfaces[]')
            surface_conditions = request.POST.getlist('surfaceConditions[]')

            # Validate required fields
            if not all([age, weight, shoe_size, prev_incidents, footwear_type, 
                       activity, usage_freq, temperature, surfaces, surface_conditions]):
                return render(request, 'index.html', {
                    'error': 'Please fill in all required fields.'
                })

            # Validate numeric fields
            if age <= 0 or weight <= 0 or shoe_size <= 0:
                return render(request, 'index.html', {
                    'error': 'Please enter valid numeric values.'
                })

            recommendations = get_recommendations(
                age, weight, shoe_size, prev_incidents, footwear_type, 
                activity, usage_freq, temperature, surfaces, surface_conditions
            )

            # No additional formatting needed, pass recommendations directly
            return render(request, 'recommendations.html', {
                'recommendations': recommendations,
                'surfaces': surfaces,
                'conditions': surface_conditions
            })
            
        except (ValueError, TypeError) as e:
            print(f"Form data error: {e}")
            print("POST data:", request.POST)
            return render(request, 'index.html', {
                'error': 'Please fill in all required fields with valid values.'
            })
    
    return render(request, 'index.html')

def index(request):
    return render(request, 'index.html')

def slip_resistance(request):
    """
    View function for the slip resistance recommender page
    """
    return render(request, 'index.html')



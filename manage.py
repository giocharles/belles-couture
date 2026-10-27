import os
import sys
import uuid
from datetime import timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='belles-final-luxury-2026',
        ROOT_URLCONF='__main__',
        ALLOWED_HOSTS = ['*'],
            CSRF_TRUSTED_ORIGINS = [
        'https://belles-couture.onrender.com',
        'https://bellescouture.shop',
        'https://www.bellescouture.shop',
    ],
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.sessions',
            '__main__',
        ],
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware'
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
            }
        },
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': []}],
        
        # --- HOSTINGER SMTP EMAIL CONFIGURATION ---
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST = 'smtp.hostinger.com',
        EMAIL_PORT = 465,  # SSL Port (Use 587 if using TLS)
        EMAIL_USE_SSL = True,  # Set to False if using port 587 with EMAIL_USE_TLS = True
        EMAIL_HOST_USER = 'support@bellescouture.shop',  # Replace with your Hostinger email
        EMAIL_HOST_PASSWORD = 'YourHostingerEmailPassword',  # Replace with your Hostinger email password
        DEFAULT_FROM_EMAIL = 'Belle\'s Couture <support@bellescouture.shop>',
    )

import django
django.setup()

from django.db import models
from django.contrib.auth.models import User
from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context
from django.middleware.csrf import get_token
from django.contrib.auth import login, logout, update_session_auth_hash
from django import forms
from django.utils import timezone
from django.core.management import call_command
from django.core.mail import send_mail

# --- MODELS ---
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=50)
    brand = models.CharField(max_length=100, default="Careline")
    image = models.CharField(max_length=500, default="")
    colors = models.CharField(max_length=300, default="Standard, Shade 1, Shade 2")
    sizes = models.CharField(max_length=300, default="Standard")
    description = models.TextField(default="Experience professional-grade beauty and flawless application crafted specifically for your daily glamour.")
    class Meta:
        app_label = '__main__'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    class Meta:
        app_label = '__main__'

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        app_label = '__main__'

class MakeupBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    service_type = models.CharField(max_length=200)
    event_type = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    additional_request = models.TextField(blank=True, default="")
    status = models.CharField(max_length=30, default="Pending Approval")
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        app_label = '__main__'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    address = models.TextField()
    phone = models.CharField(max_length=30)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default="Cash on Delivery")
    status = models.CharField(max_length=30, default="Processing")
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        app_label = '__main__'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    selected_color = models.CharField(max_length=100, blank=True, default="")
    selected_size = models.CharField(max_length=100, blank=True, default="")
    class Meta:
        app_label = '__main__'

# --- FORMS ---
class RegisterForm(forms.Form):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email Address','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        if c.get('password')!=c.get('confirm_password'):
            self.add_error('confirm_password',"Passwords don't match")
        if c.get('email') and User.objects.filter(email__iexact=c.get('email')).exists():
            self.add_error('email',"Account already exists")
        return c

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        e=c.get('email'); p=c.get('password')
        if e and p:
            try:
                u=User.objects.get(email__iexact=e)
                if not u.check_password(p):
                    self.add_error('password',"Invalid email or password")
            except User.DoesNotExist:
                self.add_error('email',"Account not found")
        return c

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Enter your account email','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        e=c.get('email')
        if e and not User.objects.filter(email__iexact=e).exists():
            self.add_error('email',"No account found with this email address")
        return c

class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'New Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm New Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        if c.get('password') != c.get('confirm_password'):
            self.add_error('confirm_password', "Passwords don't match")
        return c

class UserProfileForm(forms.Form):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':3,'style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    current_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Required only if changing password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Leave blank to keep current password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))

# --- SEED WITH 20 PRODUCTS PER BRAND (120 TOTAL) ---
def seed():
    Product.objects.all().delete()
    items = [
        # Careline
        ("Careline Oil Control Face Powder", 185, 220, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRToFG01ZZzykS64u7tMmrgtfRAT-eiWm1X1LzrSGMz-Q&s=10", "Natural, White", "10g"),
        ("Careline Best Brow Pencil", 175, 210, "Brows", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyq2aOd21QQwURDCt31ioJQoFHVoyRjQ5Wvy1yqHJdVA&s", "Gray Brown, Taupe", "Standard"),
        ("Careline Graph-Ink Liner", 220, 270, "Eyes", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS3kN6feINCOdfZII_JPE3picoegGuJI-dMpVhFHeJWf3j_C6lS6m66Iio&s", "Black", "3ml"),
        ("Careline Jelly Tint Lip & Cheek", 150, 190, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6-avXvd7TTMB-p8zx76dlq6m8MmYft2O_JNDKObuKTA&s", "Marshmallow, Just Red", "15ml"),
        ("Careline Acne Spot Concealer", 210, 250, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTyQQit2vqWPsCQnIKJoDamuNeMFxTS3dK7bWGMMIgTbQ&s=10", "Light, Medium", "6ml"),
        ("Careline Strobe Stick Highlighter", 230, 290, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQA-1d7pNbkd2PXgOuTYHmyI8YY5m4MZAqMwox9OIR1eQ&s=10", "Gold, Pink Glow", "6g"),
        ("Careline Multi-Use Palette", 350, 420, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSY32SAtYgi0Tnzq4_scR0wf3xUL5t50l7qYtpnQoq5Jg&s=10", "Universal", "12g"),
        ("Careline Scented Lip Gloss", 195, 240, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQztVYpYnkaKDzXe5Jb_zlFT4JnL21PtI2Ha6_BHbi-Bg&s=10", "Strawberry, Vanilla", "4ml"),
        ("Careline Sponge", 140, 180, "Tools", "Careline", "https://encrypted-tbn2.gstatic.com/shopping?q=tbn:ANd9GcQ2OqiQC1SxcGHJCGuR6NsrzrUPVJ5vkyahBhkF1AQz-9aW9wEgIZ1bjpxLfyUmlrbzYdlzocHhRwa0qKoe4yo7tmZ1SzhP6A", "Pink, Purple", "2pcs"),
        ("Careline Waterproof Mascara", 250, 300, "Eyes", "Careline", "https://theskincarelibrary.com/cdn/shop/files/CarelineSkinnyMascara.jpg?v=1730710406", "Black", "8ml"),
        ("Careline Matte Lipstick", 210, 260, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShf-4d1KXE2LnZSmwljOegCJc9UB34fJutiGGlSc5QyCwUb3ZMdg84RWs&s=10", "Nude, Mauve", "3.8g"),
        ("Careline Sunkissed Bronzer", 280, 340, "Face", "Careline", "https://cdn.salla.sa/aeogjR/9d6242a0-333f-4830-b2a6-5499eb97dcd8-500x500-UUnmvhgxvBf3LOdrhSkhFyWi127VpRDfIDf1MxgC.jpg", "Bronze Glow", "7g"),
        ("Careline Everyday BB Cream", 240, 299, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHMOT4PcOHnmUcqnhrsp97dxgF4zYaKyLnku4cEnmB5A&s=10", "Light, Natural", "30ml"),
        ("Careline Go Big Mascara", 260, 320, "Eyes", "Careline", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Jet Black", "9ml"),
        ("Careline Brow Gel Clear", 180, 220, "Brows", "Careline", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Clear", "5ml"),
        ("Careline Velvet Tint", 190, 240, "Lips", "Careline", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop", "Rose, Berry", "4ml"),
        ("Careline Pressed Powder Compact", 200, 250, "Face", "Careline", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Natural Beige", "10g"),
        ("Careline Sparkle Glitter Liner", 210, 260, "Eyes", "Careline", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Silver Sparkle", "3ml"),
        ("Careline Makeup Remover Wipes", 120, 150, "Skincare", "Careline", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Aloe Vera", "30 sheets"),
        ("Careline Setting Mist", 250, 310, "Setting", "Careline", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Matte Lock", "60ml"),
        # Dazzle Me
        ("Dazzle Me Ink-Liner Eyeliner", 189, 249, "Eyes", "Dazzle Me", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Super Black", "1ml"),
        ("Dazzle Me Velvet Matte Lip Cream", 159, 199, "Lips", "Dazzle Me", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Bite Size, Apple Pie", "3.5g"),
        ("Dazzle Me Get a Grip Makeup Primer", 269, 349, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Clear", "25ml"),
        ("Dazzle Me Sweet Girl Blush", 179, 229, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Mellow, Daydream", "4g"),
        ("Dazzle Me Holy Moly Eyeshadow Palette", 299, 399, "Eyes", "Dazzle Me", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Sunset, Earth", "9-Color"),
        ("Dazzle Me Better Than Filter Loose Powder", 219, 289, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Translucent", "10g"),
        ("Dazzle Me Mist Me Setting Spray", 199, 259, "Setting", "Dazzle Me", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Dewy Refresh", "60ml"),
        ("Dazzle Me Brow-To-Go Pencil", 149, 189, "Brows", "Dazzle Me", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Natural Brown", "0.3g"),
        ("Dazzle Me SOS Lip Balm", 139, 179, "Lips", "Dazzle Me", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Honey Nourish", "4g"),
        ("Dazzle Me Juicy Punch Tint", 169, 219, "Lips", "Dazzle Me", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop", "Cherry, Peach", "4ml"),
        ("Dazzle Me Joyful Glow Highlighter", 210, 270, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Champagne Glow", "5g"),
        ("Dazzle Me Constellation Eyeshadow", 320, 400, "Eyes", "Dazzle Me", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Starry Night", "10g"),
        ("Dazzle Me Daily Skin Tint", 280, 350, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Light Ivory", "30ml"),
        ("Dazzle Me Mousse Lip Cream", 170, 220, "Lips", "Dazzle Me", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Coral Mousse", "3.5g"),
        ("Dazzle Me Soft Blender Puff", 99, 130, "Tools", "Dazzle Me", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Pink", "1pc"),
        ("Dazzle Me Super Lash Mascara", 230, 290, "Eyes", "Dazzle Me", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "8ml"),
        ("Dazzle Me Poreless Primer", 290, 360, "Face", "Dazzle Me", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Matte Blur", "25ml"),
        ("Dazzle Me Quick Dry Brow Gel", 160, 200, "Brows", "Dazzle Me", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Clear", "4ml"),
        ("Dazzle Me Sugar Lip Scrub", 150, 190, "Lips", "Dazzle Me", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Vanilla Sugar", "15g"),
        ("Dazzle Me Hydrating Facial Mist", 180, 230, "Skincare", "Dazzle Me", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Rose Water", "100ml"),
        # O TWO O
        ("O.TWO.O Golden Glow Liquid Highlighter", 349, 599, "Face", "O TWO O", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Champagne Gold", "15ml"),
        ("O.TWO.O Matte Liquid Lipstick Set", 399, 699, "Lips", "O TWO O", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Nude Palette", "3pcs Set"),
        ("O.TWO.O Full Coverage Liquid Foundation", 450, 799, "Face", "O TWO O", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Ivory, Natural, Warm", "30ml"),
        ("O.TWO.O Waterproof Silk Eyeliner Pencil", 199, 350, "Eyes", "O TWO O", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Black, Brown", "1.2g"),
        ("O.TWO.O 4-in-1 Eyebrow Pen", 280, 450, "Brows", "O TWO O", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Dark Brown", "Standard"),
        ("O.TWO.O Dual-End Sculpt Contour Stick", 320, 520, "Face", "O TWO O", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Light, Medium", "4g"),
        ("O.TWO.O Silk Mascara Fiber Lengthening", 299, 499, "Eyes", "O TWO O", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "10ml"),
        ("O.TWO.O Velvet Powder Blush", 250, 400, "Face", "O TWO O", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Rose, Coral", "5g"),
        ("O.TWO.O Pore Minimizing Primer", 380, 600, "Face", "O TWO O", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Matte Clear", "30ml"),
        ("O.TWO.O Makeup Setting Spray Oil Control", 350, 580, "Setting", "O TWO O", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Matte Finish", "100ml"),
        ("O.TWO.O Matte Pressed Powder", 299, 480, "Face", "O TWO O", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Natural Ivory", "10g"),
        ("O.TWO.O Glitter Liquid Eyeshadow", 249, 420, "Eyes", "O TWO O", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Rose Gold Shimmer", "3g"),
        ("O.TWO.O Longwear Lip Gloss", 220, 380, "Lips", "O TWO O", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Clear Gloss", "4ml"),
        ("O.TWO.O Ultra Fine Brow Pencil", 180, 310, "Brows", "O TWO O", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Dark Gray", "0.1g"),
        ("O.TWO.O Face Concealer Palette", 350, 599, "Face", "O TWO O", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Correctors", "15g"),
        ("O.TWO.O Makeup Brush Set", 699, 1200, "Tools", "O TWO O", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Pink Gold", "12pcs Set"),
        ("O.TWO.O Tinted Lip Oil", 260, 450, "Lips", "O TWO O", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Honey Tint", "5ml"),
        ("O.TWO.O Volume Curling Mascara", 310, 520, "Eyes", "O TWO O", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "8ml"),
        ("O.TWO.O Makeup Remover Cleansing Balm", 390, 650, "Skincare", "O TWO O", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Standard", "100g"),
        ("O.TWO.O Matte Liquid Foundation", 420, 750, "Face", "O TWO O", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Fair, Warm Beige", "30ml"),
        # Vice Cosmetics
        ("Vice Co. Gandallier Eyebrow Pen", 245, 295, "Brows", "Vice Cosmetics", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Ash Brown, Natural", "0.5g"),
        ("Vice Co. Velvet Lip Credible", 295, 345, "Lips", "Vice Cosmetics", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Kroma, Pilya", "4g"),
        ("Vice Co. Aura Blush Collection", 225, 275, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Shalala, Flawless", "5g"),
        ("Vice Co. Endle-Slay Setting Spray", 345, 395, "Setting", "Vice Cosmetics", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Fresh Glow", "100ml"),
        ("Vice Co. Phenomenal Liquid Lipstick", 295, 345, "Lips", "Vice Cosmetics", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Tunay, Truth", "3.8g"),
        ("Vice Co. Mood Proof Eyeliner", 220, 270, "Eyes", "Vice Cosmetics", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Black", "1.5ml"),
        ("Vice Co. Zero Tinted Lip Oil", 245, 295, "Lips", "Vice Cosmetics", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Clear, Peach", "4ml"),
        ("Vice Co. Perfect Cover Concealer", 275, 325, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Fair, Light, Medium", "8g"),
        ("Vice Co. Aura Contour & Highlight", 320, 380, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Bronze/Pearl", "8g"),
        ("Vice Co. Soft Focus Pressed Powder", 295, 350, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Light Beige, Natural", "10g"),
        ("Vice Co. Grand Volumizing Mascara", 310, 370, "Eyes", "Vice Cosmetics", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "8ml"),
        ("Vice Co. Lip Liner Pencil", 180, 220, "Lips", "Vice Cosmetics", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Nude, Red", "1.2g"),
        ("Vice Co. Dewy Finish Skin Tint", 350, 420, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Light, Medium", "30ml"),
        ("Vice Co. Aura Illuminating Drops", 330, 390, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Pearl Glow", "15ml"),
        ("Vice Co. Eyebrow Soap Styler", 210, 260, "Brows", "Vice Cosmetics", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Clear", "15g"),
        ("Vice Co. Superstay Matte Lipstick", 295, 350, "Lips", "Vice Cosmetics", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Pout, Fierce", "4g"),
        ("Vice Co. Pore Blurring Primer", 340, 400, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Clear Matte", "25ml"),
        ("Vice Co. Everyday Makeup Sponge", 150, 190, "Tools", "Vice Cosmetics", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Pink", "1pc"),
        ("Vice Co. Loose HD Setting Powder", 320, 380, "Face", "Vice Cosmetics", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Translucent", "12g"),
        ("Vice Co. Colour Palette Eyeshadow", 450, 550, "Eyes", "Vice Cosmetics", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Gala Mix", "8-Color"),
        # BLK
        ("BLK Cosmetics Universal Lip Tint", 349, 399, "Lips", "BLK", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop", "All Day, Pink", "10ml"),
        ("BLK Cosmetics Daydream Airy Matte Tint", 399, 499, "Lips", "BLK", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Chic, Muse", "4g"),
        ("BLK Cosmetics All-Day Liquid Foundation", 699, 899, "Face", "BLK", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Vanilla, Beige, Warm", "30ml"),
        ("BLK Cosmetics Creamy All-Over Paint", 449, 549, "Face", "BLK", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Beach, Sunkissed", "5g"),
        ("BLK Cosmetics Sculpt & Glow Contour Palette", 599, 699, "Face", "BLK", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Duo", "12g"),
        ("BLK Cosmetics Eyebrow Pencil & Brush", 325, 385, "Brows", "BLK", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Natural Brown", "Standard"),
        ("BLK Cosmetics Long-Lasting Eyeliner", 369, 449, "Eyes", "BLK", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Intense Black", "1.2g"),
        ("BLK Cosmetics Face Setting Powder", 499, 599, "Face", "BLK", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Translucent", "10g"),
        ("BLK Cosmetics Intense Volume Mascara", 450, 550, "Eyes", "BLK", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "8ml"),
        ("BLK Cosmetics Hydrating Lip Oil", 379, 450, "Lips", "BLK", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Honey Glaze", "5ml"),
        ("BLK Cosmetics Skin Tint Sun Shield", 499, 599, "Face", "BLK", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Light, Natural", "30ml"),
        ("BLK Cosmetics Creamy Cheek Paint", 380, 450, "Face", "BLK", "https://images.unsplash.com/photo-1590156546946-ce55a12a6a5d?w=500&auto=format&fit=crop", "Rose, Peachy", "10ml"),
        ("BLK Cosmetics Matte Lipstick Deluxe", 399, 480, "Lips", "BLK", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Classic Nude", "3.8g"),
        ("BLK Cosmetics Eyebrow Mascara", 310, 370, "Brows", "BLK", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Brown Tint", "5ml"),
        ("BLK Cosmetics Full Coverage Concealer", 420, 500, "Face", "BLK", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Fair, Medium", "8ml"),
        ("BLK Cosmetics Refreshing Setting Spray", 450, 550, "Setting", "BLK", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Dewy Refresh", "100ml"),
        ("BLK Cosmetics Mini Eyeshadow Palette", 550, 680, "Eyes", "BLK", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Nude Neutrals", "6-Color"),
        ("BLK Cosmetics Double-Ended Brush", 480, 590, "Tools", "BLK", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Rose Gold", "1pc"),
        ("BLK Cosmetics Velvet Lip Butter", 360, 430, "Lips", "BLK", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Butter Pink", "4g"),
        ("BLK Cosmetics Glow Highlighting Stick", 430, 520, "Face", "BLK", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Champagne Shimmer", "6g"),
        # Ever Bilena
        ("Ever Bilena Matte Matic Lipstick", 220, 260, "Lips", "Ever Bilena", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Caramel, Vintage Red", "3.5g"),
        ("Ever Bilena Advanced Liquid Concealer", 240, 290, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Light, Medium, Dark", "10ml"),
        ("Ever Bilena Direct Universal Eye Pencil", 150, 190, "Eyes", "Ever Bilena", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Black, Dark Brown", "Standard"),
        ("Ever Bilena Face Palette Blush & Contour", 380, 450, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Warm Tones", "14g"),
        ("Ever Bilena Scenically Dewy Foundation", 350, 420, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Oriental, Natural", "30ml"),
        ("Ever Bilena Plus Hya Tinted Serum", 310, 380, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Light Tint", "20ml"),
        ("Ever Bilena Plus The Over-Acheiver Brow", 230, 280, "Brows", "Ever Bilena", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop", "Taupe, Brown", "Standard"),
        ("Ever Bilena Plus Feature Lengthening Mascara", 290, 350, "Eyes", "Ever Bilena", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black", "8ml"),
        ("Ever Bilena Maximum Setting Spray", 320, 390, "Setting", "Ever Bilena", "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop", "Matte Lock", "80ml"),
        ("Ever Bilena Matte Powder Compact", 210, 260, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Natural, Medium", "10g"),
        ("Ever Bilena Lip Gloss Crystal", 190, 240, "Lips", "Ever Bilena", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?w=500&auto=format&fit=crop", "Clear", "4ml"),
        ("Ever Bilena Eyeshadow Single", 160, 200, "Eyes", "Ever Bilena", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop", "Champagne Shimmer", "2g"),
        ("Ever Bilena Lip and Cheek Tint", 175, 220, "Lips", "Ever Bilena", "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop", "Red, Orange", "15ml"),
        ("Ever Bilena Eyebrow Powder Duo", 210, 260, "Brows", "Ever Bilena", "https://images.unsplash.com/photo-1583241799652-42135504628a?w=500&auto=format&fit=crop", "Brown Duo", "4g"),
        ("Ever Bilena Strobe Cream Highlighter", 250, 310, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1515688594390-b649af70d282?w=500&auto=format&fit=crop", "Gold Glow", "15ml"),
        ("Ever Bilena Pore Refiner Primer", 290, 360, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop", "Clear Matte", "25ml"),
        ("Ever Bilena Color Corrector Stick", 220, 270, "Face", "Ever Bilena", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Green / Peach", "4g"),
        ("Ever Bilena Precision Liquid Liner", 200, 250, "Eyes", "Ever Bilena", "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=500&auto=format&fit=crop", "Matte Black", "3ml"),
        ("Ever Bilena Complete Brush Kit", 550, 690, "Tools", "Ever Bilena", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop", "Black Set", "7pcs Set"),
        ("Ever Bilena Velvet Lipstick", 230, 280, "Lips", "Ever Bilena", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop", "Soft Pink", "3.5g"),
    ]
    for n, p, op, c, b, img, col, sz in items:
        Product.objects.create(name=n, price=p, original_price=op, category=c, brand=b, image=img, colors=col, sizes=sz)

# --- TEMPLATES & SHARED COMPONENTS ---
FONT_LINK = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
FONT_FAMILY = "'Plus Jakarta Sans', sans-serif"

TOP_BAR_HTML = """<div class="walmart-top-bar"><a href="/" class="brand-logo"><i class="bi bi-bag-heart-fill"></i> BELLE'S COUTURE</a><form class="search-container" action="/" method="GET"><input type="hidden" name="cat" value="{{cat}}"><input type="hidden" name="brand" value="{{brand}}"><input type="text" name="q" class="search-input" placeholder="Search foundation, lipstick, brushes..." value="{{q}}"><button type="submit" class="search-btn"><i class="bi bi-search"></i></button></form><div class="header-actions"><a href="/orders/" class="header-action-item"><i class="bi bi-box-seam"></i> My Orders</a><a href="/appointments/" class="header-action-item"><i class="bi bi-calendar-event"></i> Book</a>{% if user.is_staff %}<a href="/artist-admin/" class="header-action-item" style="color:#d4af37;"><i class="bi bi-shield-check"></i> Artist Admin</a>{% endif %}<a href="/profile/" class="header-action-item"><i class="bi bi-person-circle"></i> Account</a><a href="/cart/" class="header-action-item"><i class="bi bi-cart3 fs-4"></i> <span class="badge rounded-pill" style="background:#8C6D53;">{{cart_count}}</span></a><a href="/logout/" class="header-action-item"><i class="bi bi-box-arrow-right"></i></a></div></div>"""

SHARED_STYLE = "body{background:#FAF7F2; color:#3D312A; font-family:" + FONT_FAMILY + "; margin:0; padding-bottom:60px;} .walmart-top-bar{background:#FFFFFF; padding:12px 28px; display:flex; align-items:center; gap:18px; position:sticky; top:0; z-index:1000; border-bottom:1px solid #EFE8DE;} .brand-logo{font-weight:800; font-size:1.4rem; color:#6E5039; text-decoration:none;} .search-container{flex:1; max-width:680px; position:relative;} .search-input{width:100%; border-radius:24px; border:1px solid #DFD5C6; background:#FAF7F2; padding:9px 45px 9px 18px; font-size:14px; outline:none;} .search-btn{position:absolute; right:4px; top:50%; transform:translateY(-50%); background:#8C6D53; border:none; width:34px; height:34px; border-radius:50%; color:#fff;} .header-actions{display:flex; align-items:center; gap:20px; font-size:13px; font-weight:600; margin-left:auto;} .header-action-item{color:#523B29; text-decoration:none; display:flex; align-items:center; gap:6px;} .card-white{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:24px; margin-bottom:16px}"

AUTH_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>body{background:#FAF7F2; min-height:100vh; display:flex; align-items:center; justify-content:center; font-family:""" + FONT_FAMILY + """; color:#3D312A;} .box{background:#FFFFFF; border-radius:20px; padding:40px; width:100%; max-width:440px; box-shadow:0 10px 30px rgba(140,109,83,0.08); border:1px solid #EFE8DE;} h4{color:#6E5039; font-weight:800; text-align:center} .btn-y{background:#8C6D53; color:#fff; border-radius:24px; width:100%; padding:12px; border:none; font-weight:700} .alert-success{background:#F0FDF4; border:1px solid #DCFCE7; color:#166534; font-size:13px; border-radius:12px; padding:12px 14px; font-weight:700;}</style></head><body><div class="box"><h4>BELLE'S COUTURE</h4><p class="text-center fw-bold mb-3" style="font-size:14px; color:#8C7B70;">{{title}}</p>{% if success_msg %}<div class="alert alert-success text-center"><i class="bi bi-check-circle-fill me-1"></i> {{success_msg|safe}}</div>{% endif %}{% if msg %}<div class="alert alert-danger text-center small">{{msg}}</div>{% endif %}<form method="POST" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}">{% for f in form %}<div class="mb-3"><label class="form-label small fw-bold" style="color:#6E5039;">{{f.label}}</label>{{f}}{% if f.errors %}{% for err in f.errors %}<div style="color:#DC3545; font-size:12px; font-weight:600; margin-top:4px;">{{err}}</div>{% endfor %}{% endif %}</div>{% endfor %}<button class="btn-y mt-2">{{button}}</button></form><p class="text-center mt-3 small" style="color:#8C7B70;">{{footer|safe}}</p></div></body></html>"""

HOME_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Belle's Couture</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.sub-nav{background:#FFFFFF; border-bottom:1px solid #EFE8DE; padding:10px 28px; display:flex; align-items:center; gap:10px; overflow-x:auto; font-size:13px; font-weight:600;} .sub-nav-item{color:#6E5039; text-decoration:none; padding:7px 16px; border-radius:20px; background:#F5EFE6; border:1px solid #E6DCCE; white-space:nowrap;} .sub-nav-item.active{background:#8C6D53; color:#fff;} .brand-bar{background:#FFFFFF; margin:20px 28px 0 28px; border-radius:16px; padding:16px 22px; border:1px solid #EFE8DE;} .hero-grid{display:grid; grid-template-columns:2fr 1fr; gap:16px; margin:20px 28px;} @media(max-width:768px){.hero-grid{grid-template-columns:1fr;}} .main-banner{background:linear-gradient(135deg,#F3ECE1 0%,#E6DCCE 100%); border:1px solid #DFD5C6; border-radius:20px; padding:36px; min-height:240px;} 

/* ELEGANT MAKEUP ANIMATION BOX */
.makeup-animation-box{width:100%; aspect-ratio:16/9; border-radius:16px; background:radial-gradient(circle, #3d2b21 0%, #1a120e 100%); position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; border:1px solid #DFD5C6; box-shadow:inset 0 0 20px rgba(140,109,83,0.3);}
.glow-spot{position:absolute; width:120px; height:120px; background:rgba(212,175,55,0.25); border-radius:50%; filter:blur(30px); animation:pulseGlow 4s infinite alternate;}
@keyframes pulseGlow{0%{transform:scale(0.8); opacity:0.4;} 100%{transform:scale(1.4); opacity:0.9;}}
.anim-content{z-index:2; text-align:center; color:#FAF7F2; padding:12px;}
.makeup-brush-icon{font-size:2.5rem; color:#d4af37; animation:floatBrush 3s ease-in-out infinite;}
@keyframes floatBrush{0%,100%{transform:translateY(0) rotate(-10deg);} 50%{transform:translateY(-8px) rotate(10deg);}}

.product-card{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:14px; height:100%; display:flex; flex-direction:column; justify-content:space-between; transition:transform 0.2s;} .product-card:hover{transform:translateY(-3px); box-shadow:0 6px 20px rgba(140,109,83,0.1);} .product-card img{width:100%; height:160px; object-fit:cover; border-radius:12px; margin-bottom:12px;} .brand-tag{font-size:11px; font-weight:700; color:#8C6D53; text-transform:uppercase;} .product-title{font-weight:600; font-size:14px; height:38px; overflow:hidden;} .price-tag{color:#6E5039; font-weight:800; font-size:18px;} .orig-price{text-decoration:line-through; color:#A39588; font-size:12px; margin-left:6px;} .btn-view{background:#8C6D53; color:#fff; border-radius:20px; font-weight:700; border:none; width:100%; padding:8px; font-size:12px; text-align:center; display:block; text-decoration:none;} .btn-quick{background:#FAF7F2; color:#6E5039; border:1px solid #8C6D53; border-radius:20px; font-weight:700; width:100%; padding:8px; font-size:12px; text-align:center; cursor:pointer;} .btn-quick:hover{background:#F5EFE6;}</style></head><body>""" + TOP_BAR_HTML + """<div class="sub-nav"><select onchange="location = this.value;" class="form-select form-select-sm fw-bold" style="width:170px; background:#F5EFE6; border-color:#E6DCCE; color:#6E5039; border-radius:20px; padding:7px 12px; font-size:13px;"><option value="/?cat=All&brand={{brand}}">Category: All</option><option value="/?cat=Face&brand={{brand}}" {% if cat == 'Face' %}selected{% endif %}>Face & Base</option><option value="/?cat=Eyes&brand={{brand}}" {% if cat == 'Eyes' %}selected{% endif %}>Eyes</option><option value="/?cat=Lips&brand={{brand}}" {% if cat == 'Lips' %}selected{% endif %}>Lips</option><option value="/?cat=Brows&brand={{brand}}" {% if cat == 'Brows' %}selected{% endif %}>Brows</option><option value="/?cat=Setting&brand={{brand}}" {% if cat == 'Setting' %}selected{% endif %}>Setting & Sprays</option><option value="/?cat=Skincare&brand={{brand}}" {% if cat == 'Skincare' %}selected{% endif %}>Skincare & Removers</option><option value="/?cat=Tools&brand={{brand}}" {% if cat == 'Tools' %}selected{% endif %}>Tools & Accessories</option><option value="/?cat=Specialty&brand={{brand}}" {% if cat == 'Specialty' %}selected{% endif %}>Specialty & Glow</option></select><a href="/?cat={{cat}}&brand=All" class="sub-nav-item {% if brand == 'All' %}active{% endif %}">All Brands</a><a href="/?cat={{cat}}&brand=Careline" class="sub-nav-item {% if brand == 'Careline' %}active{% endif %}">Careline</a><a href="/?cat={{cat}}&brand=Dazzle Me" class="sub-nav-item {% if brand == 'Dazzle Me' %}active{% endif %}">Dazzle Me</a><a href="/?cat={{cat}}&brand=O TWO O" class="sub-nav-item {% if brand == 'O TWO O' %}active{% endif %}">O.TWO.O</a><a href="/?cat={{cat}}&brand=Vice Cosmetics" class="sub-nav-item {% if brand == 'Vice Cosmetics' %}active{% endif %}">Vice Cosmetics</a><a href="/?cat={{cat}}&brand=BLK" class="sub-nav-item {% if brand == 'BLK' %}active{% endif %}">BLK</a><a href="/?cat={{cat}}&brand=Ever Bilena" class="sub-nav-item {% if brand == 'Ever Bilena' %}active{% endif %}">Ever Bilena</a></div><div class="hero-grid"><div class="main-banner"><h1 style="font-weight:800; color:#523B29;">Belle's Complete Beauty Essentials</h1><p>Explore professional makeup products ranging from primers, foundations, to brushes and setting sprays!</p><a href="/appointments/" class="btn rounded-pill px-4 fw-bold" style="background:#6E5039; color:#fff;"><i class="bi bi-stars"></i> Book Makeup Artist</a></div><div style="background:#fff; border-radius:20px; padding:16px; border:1px solid #EFE8DE; display:flex; flex-direction:column; justify-content:center; align-items:center;"><div class="makeup-animation-box"><div class="glow-spot"></div><div class="anim-content"><div class="makeup-brush-icon"><i class="bi bi-magic"></i></div><h6 class="fw-bold mt-2" style="color:#d4af37; letter-spacing:1px;">LUXE GLAMOUR ANIMATION</h6><p class="small text-muted m-0" style="color:#D4C5B9!important; font-size:11px;">Flawless Radiance & Artistry in Motion</p></div></div><span class="small fw-bold mt-2" style="color:#523B29;"><i class="bi bi-stars" style="color:#8C6D53;"></i> Belle's Signature Artistry Showcase</span></div></div><div class="brand-bar"><h6 class="fw-bold" style="color:#6E5039;"><i class="bi bi-tags-fill"></i> Showing <b>{{products|length}}</b> products</h6></div><div class="container-fluid px-4 mt-4"><div class="row g-3">{% for p in products %}<div class="col-6 col-md-4 col-lg-3"><div class="product-card"><div><img src="{{p.image}}"><div class="brand-tag">{{p.brand}}</div><div class="product-title">{{p.name}}</div></div><div><div><span class="price-tag">₱{{p.price}}</span>{% if p.original_price %}<span class="orig-price">₱{{p.original_price}}</span>{% endif %}</div><div class="d-grid gap-2 mt-2"><button type="button" class="btn-quick" data-bs-toggle="modal" data-bs-target="#quickModal{{p.id}}"><i class="bi bi-bag-plus"></i> Quick Shop</button><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><button type="submit" class="btn w-100 rounded-pill fw-bold py-1" style="background:#8C6D53; color:#fff; font-size:12px;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form><a href="/product/{{p.id}}/" class="btn-view">View Details</a></div></div></div></div><!-- Quick Shop Modal --><div class="modal fade" id="quickModal{{p.id}}" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4 border-0" style="background:#FAF7F2;"><div class="modal-header border-0 pb-0"><h5 class="modal-title fw-bold" style="color:#6E5039;">Quick Shop</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><div class="d-flex gap-3 align-items-center mb-3"><img src="{{p.image}}" style="width:90px; height:90px; object-fit:cover; border-radius:12px;"><div><b style="color:#523B29;">{{p.name}}</b><div class="fs-5 fw-bold mt-1" style="color:#6E5039;">₱{{p.price}}</div></div></div><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Shade / Variant</label><select name="color" class="form-select form-select-sm" style="background:#FAF7F2; border-color:#DFD5C6; border-radius:10px;"><option value="Standard">Standard</option><option value="Shade 1">Shade 1</option><option value="Shade 2">Shade 2</option></select></div><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Quantity</label><input type="number" name="quantity" value="1" min="1" max="10" class="form-control form-control-sm" style="background:#FAF7F2; border-color:#DFD5C6; border-radius:10px;"></div><button type="submit" class="btn w-100 rounded-pill fw-bold py-2 mt-2" style="background:#8C6D53; color:#fff;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form></div></div></div></div>{% endfor %}</div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

PRODUCT_DETAIL_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{product.name}}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-primary-y{background:#8C6D53; color:#fff; border-radius:24px; border:none; padding:12px; font-weight:700; width:100%} .form-select, .form-control{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:12px; padding:10px 14px;}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-5"><div class="row g-5 align-items-center"><div class="col-md-6"><div class="card-white p-3 text-center"><img src="{{product.image}}" style="width:100%; max-height:420px; object-fit:cover; border-radius:16px;"></div></div><div class="col-md-6"><div class="card-white"><span class="badge mb-2" style="background:#8C6D53; font-size:11px;">{{product.brand}} | {{product.category}}</span><h2 class="fw-bold" style="color:#523B29;">{{product.name}}</h2><div class="mb-3"><span class="fs-3 fw-bold" style="color:#6E5039;">₱{{product.price}}</span>{% if product.original_price %}<span class="text-decoration-line-through text-muted ms-2">₱{{product.original_price}}</span>{% endif %}</div><p class="text-muted small mb-4">{{product.description}}</p><form method="POST" action="/add-to-cart/{{product.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;"><i class="bi bi-palette"></i> Choose Shade / Variant</label><select name="color" class="form-select">{% for col in color_list %}<option value="{{col}}">{{col}}</option>{% endfor %}</select></div><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;"><i class="bi bi-rulers"></i> Choose Size / Edition</label><select name="size" class="form-select">{% for sz in size_list %}<option value="{{sz}}">{{sz}}</option>{% endfor %}</select></div><div class="mb-4"><label class="fw-bold small mb-1" style="color:#6E5039;"><i class="bi bi-plus-slash-minus"></i> Quantity</label><input type="number" name="quantity" value="1" min="1" max="10" class="form-control"></div><button type="submit" class="btn-primary-y"><i class="bi bi-bag-plus"></i> Add to Cart</button></form></div></div></div></div></body></html>"""

PROFILE_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Account Dashboard</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-y{background:#8C6D53; color:#fff; border-radius:24px; width:100%; padding:12px; border:none; font-weight:700;} .info-display-box{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:12px; padding:12px 16px; margin-bottom:16px;} .edit-field{display:none;}</style><script>function toggleEditMode(){let viewMode = document.getElementById('view_mode');let editMode = document.getElementById('edit_mode');let editBtn = document.getElementById('edit_btn_icon');if(editMode.style.display === 'none'){viewMode.style.display = 'none';editMode.style.display = 'block';editBtn.className = 'bi bi-x-lg';}else{viewMode.style.display = 'block';editMode.style.display = 'none';editBtn.className = 'bi bi-pencil-square';}}</script></head><body>""" + TOP_BAR_HTML + """<div class="container my-5" style="max-width:960px;"><div class="row g-4"><!-- Left Sidebar Navigation --><div class="col-lg-4"><div class="card-white text-center"><div class="mb-3"><div class="rounded-circle d-inline-flex align-items-center justify-content-center fw-bold fs-3" style="width:72px; height:72px; background:#F5EFE6; color:#6E5039; border:2px solid #DFD5C6;"><i class="bi bi-person-fill"></i></div></div><h5 class="fw-bold mb-1" style="color:#523B29;">{{user.first_name}}</h5><p class="text-muted small mb-3">{{user.email}}</p><div class="d-grid gap-2 text-start mt-4"><a href="/orders/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#6E5039; border-color:#DFD5C6;"><i class="bi bi-box-seam me-2"></i> View My Orders</a><a href="/appointments/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#6E5039; border-color:#DFD5C6;"><i class="bi bi-calendar-event me-2"></i> My Artist Bookings</a>{% if user.is_staff %}<a href="/artist-admin/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#d4af37; border-color:#DFD5C6;"><i class="bi bi-shield-check me-2"></i> Artist Admin Dashboard</a>{% endif %}<a href="/logout/" class="btn btn-sm btn-outline-danger rounded-pill py-2 px-3 fw-bold text-start"><i class="bi bi-box-arrow-right me-2"></i> Log Out</a></div></div></div><!-- Right Main Content --><div class="col-lg-8"><div class="card-white"><div class="d-flex justify-content-between align-items-center mb-3"><div><h4 class="fw-bold m-0" style="color:#6E5039;"><i class="bi bi-person-gear"></i> Account Settings & Profile</h4><p class="text-muted small m-0">Your personal details are secured and permanent. Click edit to update.</p></div><button type="button" class="btn btn-sm rounded-circle d-flex align-items-center justify-content-center shadow-sm" style="width:38px; height:38px; background:#F5EFE6; color:#6E5039; border:1px solid #DFD5C6;" onclick="toggleEditMode()" title="Edit Information"><i id="edit_btn_icon" class="bi bi-pencil-square fs-6"></i></button></div><hr>{% if success_msg %}<div class="alert alert-success rounded-3 mb-4"><i class="bi bi-check-circle-fill me-1"></i> {{success_msg}}</div>{% endif %}{% if msg %}<div class="alert alert-danger rounded-3 mb-4"><i class="bi bi-exclamation-triangle-fill me-1"></i> {{msg}}</div>{% endif %}<!-- READ-ONLY VIEW MODE --><div id="view_mode"><div class="mb-3"><label class="fw-bold small text-muted">Full Name</label><div class="info-display-box fw-bold" style="color:#523B29;">{% if user.first_name %}{{user.first_name}}{% else %}Not set{% endif %}</div></div><div class="mb-3"><label class="fw-bold small text-muted">Email Address</label><div class="info-display-box fw-bold" style="color:#523B29;">{{user.email}}</div></div><div class="mb-3"><label class="fw-bold small text-muted">Phone Number</label><div class="info-display-box fw-bold" style="color:#523B29;">{% if profile.phone %}{{profile.phone}}{% else %}Not set{% endif %}</div></div><div class="mb-3"><label class="fw-bold small text-muted">Address</label><div class="info-display-box fw-bold" style="color:#523B29;">{% if profile.address %}{{profile.address}}{% else %}Not set{% endif %}</div></div><div class="mb-3"><label class="fw-bold small text-muted">City</label><div class="info-display-box fw-bold" style="color:#523B29;">{% if profile.city %}{{profile.city}}{% else %}Not set{% endif %}</div></div></div><!-- EDITABLE FORM MODE --><div id="edit_mode" style="display:none;"><form method="POST"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="row g-3">{% for f in form %}<div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">{{f.label}}</label>{{f}}{% if f.errors %}{% for err in f.errors %}<div style="color:#DC3545; font-size:12px; margin-top:4px;">{{err}}</div>{% endfor %}{% endif %}</div>{% endfor %}</div><button class="btn-y mt-4">Save Changes</button></form></div></div></div></div></div></body></html>"""

CART_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cart</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-blue{background:#8C6D53; color:#fff; border-radius:24px; border:none; padding:12px; font-weight:700; width:100%} .product-card{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:14px; height:100%; display:flex; flex-direction:column; justify-content:space-between;} .product-card img{width:100%; height:130px; object-fit:cover; border-radius:12px; margin-bottom:10px;} .brand-tag{font-size:10px; font-weight:700; color:#8C6D53; text-transform:uppercase;} .product-title{font-weight:600; font-size:13px; height:34px; overflow:hidden;} .price-tag{color:#6E5039; font-weight:800; font-size:16px;} .btn-quick{background:#FAF7F2; color:#6E5039; border:1px solid #8C6D53; border-radius:20px; font-weight:700; width:100%; padding:6px; font-size:11px; text-align:center; cursor:pointer;}</style><script>function toggleAddressMode(){let mode = document.querySelector('input[name="address_mode"]:checked').value;let customDiv = document.getElementById('custom_address_section');if(mode === 'custom'){customDiv.style.display = 'block';document.getElementById('c_addr').required = true;}else{customDiv.style.display = 'none';document.getElementById('c_addr').required = false;}}</script></head><body>""" + TOP_BAR_HTML + """<div class="container my-4"><div class="row"><div class="col-lg-7"><div class="card-white"><h5 class="fw-bold" style="color:#6E5039;">Shopping Cart ({{count}} items)</h5><hr>{% if items %}{% for it in items %}<div class="d-flex gap-3 py-3 border-bottom"><img style="width:80px; height:80px; object-fit:cover; border-radius:10px;" src="{{it.product.image}}"><div class="flex-grow-1"><div class="fw-bold">{{it.product.name}}</div><small class="text-muted">{{it.product.brand}}</small><div class="small mt-1" style="color:#8C7B70;">{% if it.color %}Shade: <b>{{it.color}}</b>{% endif %}{% if it.size %} | Size: <b>{{it.size}}</b>{% endif %}</div><div class="mt-2"><span class="badge bg-light text-dark border">Qty: {{it.qty}}</span><a href="/remove/{{it.index}}/" class="btn btn-sm btn-outline-danger rounded-pill ms-2" style="font-size:11px">Remove</a></div></div><div class="fw-bold" style="color:#6E5039;">₱{{it.subtotal}}</div></div>{% endfor %}<div class="text-end mt-3"><h5 class="fw-bold">Subtotal: <span style="color:#6E5039;">₱{{total}}</span></h5></div>{% else %}<div class="text-center py-5"><h6>Your cart is empty</h6><a href="/" class="btn rounded-pill mt-2" style="background:#8C6D53; color:#fff;">Shop Now</a></div>{% endif %}</div></div><div class="col-lg-5"><div class="card-white"><h6 class="fw-bold" style="color:#6E5039;">Cash On Delivery Checkout</h6>{% if items %}<form method="POST" action="/checkout/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="small fw-bold">Full Name</label><input class="form-control form-control-sm" name="full_name" value="{{user.first_name}}" required></div><div class="mb-3"><label class="small fw-bold mb-2">Delivery Address & Contact</label><div class="form-check"><input class="form-check-input" type="radio" name="address_mode" id="use_profile" value="profile" checked onchange="toggleAddressMode()"><label class="form-check-label small" for="use_profile">Use Account Info <br><span class="text-muted" style="font-size:11px;">(Phone: <b>{% if profile.phone %}{{profile.phone}}{% else %}Not set{% endif %}</b>, Address: <b>{% if profile.address %}{{profile.address}}, {{profile.city}}{% else %}Not set{% endif %}</b>)</span></label></div><div class="form-check mt-2"><input class="form-check-input" type="radio" name="address_mode" id="use_custom" value="custom" onchange="toggleAddressMode()"><label class="form-check-label small" for="use_custom">Use Another Address</label></div></div><div id="custom_address_section" style="display:none;" class="mb-3 p-3 rounded-3" style="background:#FAF7F2; border:1px solid #DFD5C6;"><div class="mb-2"><label class="small fw-bold">Alternate Phone</label><input class="form-control form-control-sm" name="alt_phone" placeholder="Phone Number"></div><div><label class="small fw-bold">Alternate Address & City</label><textarea class="form-control form-control-sm" name="alt_address" id="c_addr" rows="2" placeholder="Street, Barangay, City"></textarea></div></div><hr><div class="d-flex justify-content-between fw-bold mb-3"><span>Total</span><span style="color:#6E5039;">₱{{total}}</span></div><button class="btn-blue">Place Order - COD</button></form>{% endif %}</div></div></div><!-- Bottom Product Suggestions Section --><div class="row mt-5"><div class="col-12"><div class="card-white"><h5 class="fw-bold mb-4" style="color:#6E5039;"><i class="bi bi-stars"></i> You May Also Like / Add More Products</h5><div class="row g-3">{% for p in products %}<div class="col-6 col-md-3"><div class="product-card"><div><img src="{{p.image}}"><div class="brand-tag">{{p.brand}}</div><div class="product-title">{{p.name}}</div></div><div class="mt-2"><div><span class="price-tag">₱{{p.price}}</span></div><div class="d-grid gap-2 mt-2"><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><button type="submit" class="btn w-100 rounded-pill fw-bold py-1" style="background:#8C6D53; color:#fff; font-size:11px;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form><a href="/product/{{p.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill py-0" style="font-size:11px;">View</a></div></div></div></div>{% endfor %}</div></div></div></div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

ORDER_SUCCESS_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">""" + FONT_LINK + """<style>body{background:#FAF7F2; display:flex; align-items:center; justify-content:center; min-height:100vh; font-family:""" + FONT_FAMILY + """;} .success-card{background:#fff; border-radius:24px; border:1px solid #EFE8DE; padding:40px; max-width:550px; width:100%; text-align:center;}</style></head><body><div class="success-card"><h3 class="fw-bold" style="color:#6E5039;">Order Placed Successfully!</h3><div class="p-3 text-start rounded-3 mb-4" style="background:#FAF7F2; border:1px solid #EFE8DE;"><div class="d-flex justify-content-between"><b>Order ID:</b> <span>#{{order.id}}</span></div><div class="d-flex justify-content-between"><b>Total:</b> <span>₱{{order.total_amount}}</span></div></div><a href="/orders/" class="btn rounded-pill px-4" style="background:#8C6D53; color:#fff;">View Order</a> <a href="/" class="btn rounded-pill px-4 border ms-2">Continue Shopping</a></div></body></html>"""

ORDERS_DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Orders Dashboard</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.order-card{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:16px; padding:20px; margin-bottom:20px; transition:all 0.2s;} .order-card:hover{box-shadow:0 6px 18px rgba(140,109,83,0.08);} .item-row{display:flex; align-items:center; gap:14px; padding:10px 0; border-bottom:1px dashed #E6DCCE;} .item-row:last-child{border-bottom:none;} .status-badge{font-size:11px; font-weight:700; padding:6px 12px; border-radius:20px; text-transform:uppercase;}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-4" style="max-width:880px;"><div class="card-white"><div class="mb-3"><h4 class="fw-bold m-0" style="color:#6E5039;"><i class="bi bi-box-seam"></i> My Orders Dashboard</h4></div><p class="text-muted small mb-4">Review your purchase history, check delivery details, or manage order statuses.</p><hr>{% if orders %}{% for o in orders %}<div class="order-card"><div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom"><div><h6 class="fw-bold mb-1" style="color:#6E5039;">Order #{{o.id}}</h6><small class="text-muted"><i class="bi bi-clock"></i> Placed on {{o.created_at|date:"M d, Y"}}</small></div><div>{% if o.status == 'Cancelled' %}<span class="status-badge bg-danger text-white"><i class="bi bi-x-circle"></i> Cancelled</span>{% else %}<span class="status-badge" style="background:#E2E8F0; color:#1E293B;"><i class="bi bi-hourglass-split"></i> {{o.status}}</span>{% endif %}</div></div><div class="my-3">{% for item in o.items.all %}<div class="item-row"><img src="{{item.product.image}}" style="width:56px; height:56px; object-fit:cover; border-radius:10px; border:1px solid #DFD5C6;"><div class="flex-grow-1"><div class="fw-bold" style="color:#523B29; font-size:14px;">{{item.product.name}}</div><div class="small text-muted">{% if item.selected_color %}Shade: <b>{{item.selected_color}}</b>{% endif %}{% if item.selected_size %} | Size: <b>{{item.selected_size}}</b>{% endif %} | Qty: <b>{{item.quantity}}</b></div></div><div class="fw-bold" style="color:#6E5039;">₱{{item.price}}</div></div>{% endfor %}</div><div class="p-3 rounded-3 mb-3" style="background:#FFFFFF; border:1px solid #E6DCCE;"><div class="row small"><div class="col-md-7"><b>Delivery Address:</b><br><span class="text-muted">{{o.full_name}} — {{o.address}} (Ph: {{o.phone}})</span></div><div class="col-md-5 text-md-end mt-2 mt-md-0"><span class="text-muted">Total Amount:</span><br><span class="fs-5 fw-bold" style="color:#6E5039;">₱{{o.total_amount}}</span></div></div></div><div class="d-flex justify-content-end gap-2">{% if o.status != 'Cancelled' %}<a href="/cancel-order/{{o.id}}/" class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-bold" onclick="return confirm('Are you sure you want to cancel this order?');"><i class="bi bi-x-circle me-1"></i> Cancel Order</a>{% else %}<a href="/delete-order/{{o.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill px-3 fw-bold"><i class="bi bi-trash me-1"></i> Remove from History</a>{% endif %}</div></div>{% endfor %}{% else %}<div class="text-center py-5"><div class="mb-3 fs-1 text-muted"><i class="bi bi-bag-x"></i></div><h6 class="fw-bold" style="color:#523B29;">No orders placed yet</h6><p class="text-muted small">Explore our professional beauty collection and place your first order!</p><a href="/" class="btn rounded-pill px-4 fw-bold mt-2" style="background:#8C6D53; color:#fff;">Start Shopping</a></div>{% endif %}</div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

APPOINTMENT_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bookings</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-blue{background:#8C6D53; color:#fff; border-radius:24px; border:none; padding:12px; font-weight:700; width:100%} .package-card{display:block; padding:16px; border-radius:12px; background:#FAF7F2; border:1px solid #DFD5C6; cursor:pointer} .package-card input{display:none} .package-card:has(input:checked){background:#F5EFE6; border-color:#8C6D53; box-shadow:0 0 0 1px #8C6D53} .booking-card{background:#FAF7F2; border:1px solid #EFE8DE; border-radius:12px; padding:16px; margin-bottom:12px}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-4"><div class="row"><div class="col-lg-8"><div class="card-white"><h4 class="fw-bold" style="color:#6E5039;">Book Your Makeup Artist</h4>{% if success %}<div class="alert alert-success rounded-3">{{success}}</div>{% endif %}<form method="POST"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><h6 class="fw-bold mt-4 mb-3">1. Select Service Package</h6><div class="row g-2"><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Graduation Glam" checked><div class="fw-bold">Graduation Glam</div><small>₱2,500 | Full Lash & Hair</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Normal Day Natural"><div class="fw-bold">Normal Day Natural</div><small>₱1,500 | Fresh Everyday</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Event Glam"><div class="fw-bold">Event Glam</div><small>₱3,000 | Party & Gala</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Bridal Glow"><div class="fw-bold">Bridal Glow</div><small>₱4,500 | Weddings</small></label></div></div><h6 class="fw-bold mt-4">2. Date & Details</h6><div class="row g-2"><div class="col-6"><input type="date" name="date" class="form-control" required min="{{today}}"></div><div class="col-6"><input type="time" name="time" class="form-control" required></div></div><h6 class="fw-bold mt-4">3. Customer Info</h6><div class="row g-2"><div class="col-12"><input name="customer_name" class="form-control" value="{{user.first_name}} {{user.last_name}}" placeholder="Full Name" required></div><div class="col-6"><input name="email" type="email" class="form-control" value="{{user.email}}" placeholder="Email" required></div><div class="col-6"><input name="phone" class="form-control" placeholder="Phone" value="{{profile.phone}}" required></div><div class="col-12"><input name="address" class="form-control" placeholder="Complete Address" value="{{profile.address}}" required></div><div class="col-6"><input name="city" class="form-control" placeholder="City" value="{{profile.city}}" required></div><div class="col-6"><input name="event_type" class="form-control" placeholder="Event Category (e.g. Graduation)" required></div><div class="col-12"><textarea name="additional_request" class="form-control" placeholder="Additional requests" rows="3"></textarea></div></div><button class="btn-blue mt-4">Confirm Booking</button></form></div></div><div class="col-lg-4"><div class="card-white"><h6 class="fw-bold mb-3" style="color:#6E5039;"><i class="bi bi-calendar-check"></i> Your Bookings</h6>{% if bookings %}{% for b in bookings %}<div class="booking-card"><div class="d-flex justify-content-between align-items-start"><div><b class="small" style="color:#6E5039;">{{b.service_type}}</b><div class="small text-muted mt-1"><i class="bi bi-calendar"></i> Date: {{b.date}}<br><i class="bi bi-geo-alt"></i> City: {{b.city}}</div></div><span class="badge {% if b.status == 'Cancelled' %}bg-danger{% elif b.status == 'Accepted' %}bg-success{% else %}bg-warning text-dark{% endif %}" style="font-size:10px;">{{b.status}}</span></div>{% if b.status == 'Cancelled' and b.cancelled_at %}<div class="mt-2 p-2 rounded-2 small" style="background:#FEE2E2; border:1px solid #FECACA; color:#991B1B;"><i class="bi bi-x-circle-fill"></i> <b>Cancelled on:</b> {{b.cancelled_at|date:"M d, Y"}}</div>{% endif %}<div class="d-grid gap-2 mt-3"><button class="btn btn-sm rounded-pill fw-bold" data-bs-toggle="modal" data-bs-target="#detailsModal{{b.id}}" style="background:#fff; border:1px solid #8C6D53; color:#6E5039;"><i class="bi bi-eye"></i> Review Details</button>{% if b.status != 'Cancelled' %}<a href="/cancel-booking/{{b.id}}/" class="btn btn-sm btn-outline-danger rounded-pill">Cancel</a>{% else %}<a href="/delete-booking/{{b.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill">Delete</a>{% endif %}</div></div><div class="modal fade" id="detailsModal{{b.id}}" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4"><div class="modal-header border-0" style="background:#FAF7F2;"><h6 class="modal-title fw-bold" style="color:#6E5039;"><i class="bi bi-receipt"></i> Booking Details #{{b.id}}</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body small"><div class="row g-2"><div class="col-12"><b>Service:</b> {{b.service_type}}</div><div class="col-6"><b>Event Type:</b> {{b.event_type}}</div><div class="col-6"><b>Status:</b> <span class="badge {% if b.status == 'Cancelled' %}bg-danger{% elif b.status == 'Accepted' %}bg-success{% else %}bg-warning text-dark{% endif %}">{{b.status}}</span></div><div class="col-6"><b>Date:</b> {{b.date}}</div><div class="col-6"><b>Time:</b> {{b.time}}</div><hr class="my-2"><div class="col-12"><b>Customer:</b> {{b.customer_name}}</div><div class="col-12"><b>Email:</b> {{b.email}}</div><div class="col-12"><b>Phone:</b> {{b.phone}}</div><div class="col-12"><b>Address:</b> {{b.address}}</div><div class="col-12"><b>City:</b> {{b.city}}</div><div class="col-12"><b>Additional Request:</b><br><em>{% if b.additional_request %}{{b.additional_request}}{% else %}None{% endif %}</em></div><hr class="my-2"><div class="col-12"><b>Booked On:</b> {{b.created_at|date:"M d, Y"}}</div>{% if b.status == 'Cancelled' and b.cancelled_at %}<div class="col-12 mt-2 p-2 rounded-2" style="background:#FEE2E2; border:1px solid #FECACA; color:#991B1B;"><b><i class="bi bi-exclamation-triangle-fill"></i> Cancelled Date:</b> {{b.cancelled_at|date:"M d, Y"}}</div>{% endif %}</div></div><div class="modal-footer border-0"><button type="button" class="btn btn-sm rounded-pill px-3" style="background:#8C6D53; color:#fff;" data-bs-dismiss="modal">Close</button></div></div></div></div>{% endfor %}{% else %}<p class="small text-muted text-center py-3">No bookings yet</p>{% endif %}</div></div></div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

ARTIST_ADMIN_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Artist Admin - All Reservations</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.admin-card{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:16px; padding:20px; margin-bottom:16px;}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-4" style="max-width:960px;"><div class="card-white"><div class="d-flex justify-content-between align-items-center mb-4"><div><h4 class="fw-bold m-0" style="color:#6E5039;"><i class="bi bi-shield-check"></i> Makeup Artist Administration Hub</h4><p class="text-muted small m-0">Review all customer reservations and manage appointments.</p></div><span class="badge rounded-pill px-3 py-2 fw-bold" style="background:#F5EFE6; color:#6E5039; border:1px solid #DFD5C6;">Total Reservations: {{bookings|length}}</span></div><hr>{% if bookings %}{% for b in bookings %}<div class="admin-card"><div class="row align-items-center"><div class="col-md-7"><div class="d-flex align-items-center gap-2 mb-1"><h5 class="fw-bold m-0" style="color:#523B29;">{{b.customer_name}}</h5><span class="badge {% if b.status == 'Accepted' %}bg-success{% elif b.status == 'Cancelled' %}bg-danger{% else %}bg-warning text-dark{% endif %}" style="font-size:11px;">{{b.status}}</span></div><div class="small fw-bold" style="color:#8C6D53;"><i class="bi bi-stars"></i> Package: {{b.service_type}} ({{b.event_type}})</div><div class="small text-muted mt-1"><i class="bi bi-calendar-event"></i> Date: <b>{{b.date}}</b> at {{b.time}}<br><i class="bi bi-geo-alt"></i> Location: {{b.address}}, {{b.city}}<br><i class="bi bi-telephone"></i> Contact: {{b.phone}} | <i class="bi bi-envelope"></i> {{b.email}}</div>{% if b.additional_request %}<div class="small mt-2 p-2 rounded-2" style="background:#FFF; border:1px solid #EFE8DE;"><b>Request:</b> <em>{{b.additional_request}}</em></div>{% endif %}</div><div class="col-md-5 text-md-end mt-3 mt-md-0"><div class="d-flex flex-column gap-2">{% if b.status != 'Accepted' %}<a href="/artist-admin/status/{{b.id}}/Accepted/" class="btn btn-sm rounded-pill fw-bold" style="background:#198754; color:#fff;"><i class="bi bi-check-circle"></i> Accept Reservation</a>{% endif %}{% if b.status != 'Completed' and b.status != 'Cancelled' %}<a href="/artist-admin/status/{{b.id}}/Completed/" class="btn btn-sm rounded-pill fw-bold" style="background:#6E5039; color:#fff;"><i class="bi bi-flag-fill"></i> Mark Completed</a>{% endif %}{% if b.status != 'Cancelled' %}<a href="/artist-admin/status/{{b.id}}/Cancelled/" class="btn btn-sm btn-outline-danger rounded-pill fw-bold"><i class="bi bi-x-circle"></i> Decline / Cancel</a>{% endif %}</div></div></div></div>{% endfor %}{% else %}<div class="text-center py-5"><div class="mb-3 fs-1 text-muted"><i class="bi bi-calendar-x"></i></div><h6 class="fw-bold" style="color:#523B29;">No customer reservations yet</h6><p class="text-muted small">Reservations booked by customers will appear here for review and acceptance.</p></div>{% endif %}</div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

# --- HELPERS ---
def get_cart(request):
    return request.session.get('cart', [])

def cart_count(request):
    cart = get_cart(request)
    return len(cart)

def render_template(html, ctx, request):
    csrf_token = get_token(request)
    if request.user.is_authenticated:
        user_obj = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
    else:
        user_obj = type('obj', (object,), {
            'first_name': 'Guest',
            'last_name': '',
            'email': '',
            'is_authenticated': False,
            'is_staff': False
        })()
        profile = type('obj', (object,), {
            'phone': '',
            'address': '',
            'city': ''
        })()
    ctx['csrf'] = csrf_token
    ctx['user'] = user_obj
    ctx['profile'] = profile
    ctx['cart_count'] = cart_count(request)
    if 'cat' not in ctx:
        ctx['cat'] = request.GET.get('cat', 'All')
    if 'brand' not in ctx:
        ctx['brand'] = request.GET.get('brand', 'All')
    if 'q' not in ctx:
        ctx['q'] = request.GET.get('q', '')
    if 'success_msg' not in ctx:
        ctx['success_msg'] = None
    if 'msg' not in ctx:
        ctx['msg'] = None
    return Template(html).render(Context(ctx))

# --- VIEWS ---
def home(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    q=request.GET.get('q','')
    cat=request.GET.get('cat','All')
    brand=request.GET.get('brand','All')
    products=Product.objects.all()
    if q:
        products=products.filter(name__icontains=q)
    if cat!='All':
        products=products.filter(category=cat)
    if brand!='All':
        products=products.filter(brand=brand)
    html=render_template(HOME_HTML, {'products':products,'q':q,'cat':cat,'brand':brand}, request)
    return HttpResponse(html)

def product_detail(request, pid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return HttpResponseRedirect('/')
    
    color_list = [c.strip() for c in product.colors.split(',') if c.strip()]
    size_list = [s.strip() for s in product.sizes.split(',') if s.strip()]
    
    html = render_template(PRODUCT_DETAIL_HTML, {
        'product': product,
        'color_list': color_list,
        'size_list': size_list,
        'cat': 'All',
        'brand': 'All'
    }, request)
    return HttpResponse(html)

def profile_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    success_msg = None
    msg = None
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            new_email = cd['email']
            # Check if email is taken by another user
            if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
                msg = "This email address is already in use by another account."
            else:
                request.user.first_name = cd['full_name']
                request.user.email = new_email
                request.user.username = new_email  # Keeping username in sync with email login
                
                # Handle password update if requested
                new_pw = cd.get('new_password')
                curr_pw = cd.get('current_password')
                if new_pw:
                    if not curr_pw or not request.user.check_password(curr_pw):
                        msg = "Please provide your correct current password to set a new password."
                    else:
                        request.user.set_password(new_pw)
                        request.user.save()
                        update_session_auth_hash(request, request.user)
                        success_msg = "Account and password updated successfully!"
                
                if not msg:
                    request.user.save()
                    profile.phone = cd['phone']
                    profile.address = cd['address']
                    profile.city = cd['city']
                    profile.save()
                    if not success_msg:
                        success_msg = "Account updated successfully!"
        else:
            msg = "Please correct the errors below."
    else:
        form = UserProfileForm(initial={
            'full_name': request.user.first_name,
            'email': request.user.email,
            'phone': profile.phone,
            'address': profile.address,
            'city': profile.city
        })
    html = render_template(PROFILE_HTML, {'form': form, 'success_msg': success_msg, 'msg': msg}, request)
    return HttpResponse(html)

def add_to_cart(request, pid):
    if request.method == 'POST':
        color = request.POST.get('color', 'Standard')
        size = request.POST.get('size', 'Standard')
        qty = int(request.POST.get('quantity', 1))
    else:
        color = 'Standard'
        size = 'Standard'
        qty = 1

    cart = request.session.get('cart', [])
    found = False
    for item in cart:
        if str(item['pid']) == str(pid) and item.get('color') == color and item.get('size') == size:
            item['qty'] += qty
            found = True
            break
            
    if not found:
        cart.append({
            'pid': int(pid),
            'qty': qty,
            'color': color,
            'size': size
        })
        
    request.session['cart'] = cart
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cart/'))

def remove_from_cart(request, index):
    cart = request.session.get('cart', [])
    try:
        idx = int(index)
        if 0 <= idx < len(cart):
            cart.pop(idx)
    except:
        pass
    request.session['cart'] = cart
    return HttpResponseRedirect('/cart/')

def cart_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    cart = get_cart(request)
    items = []
    total = 0
    for idx, item in enumerate(cart):
        try:
            p = Product.objects.get(id=item['pid'])
            qty = item.get('qty', 1)
            subtotal = float(p.price) * qty
            total += subtotal
            items.append({
                'index': idx,
                'product': p,
                'qty': qty,
                'color': item.get('color', ''),
                'size': item.get('size', ''),
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            pass
            
    products = Product.objects.all()[:8]
    html = render_template(CART_HTML, {
        'items': items, 
        'total': total, 
        'count': len(items), 
        'products': products,
        'cat': 'All', 
        'brand': 'All', 
        'q': ''
    }, request)
    return HttpResponse(html)

def checkout(request):
    if request.method == 'POST':
        cart = get_cart(request)
        if not cart:
            return HttpResponseRedirect('/cart/')
        
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        address_mode = request.POST.get('address_mode', 'profile')
        
        if address_mode == 'custom':
            phone = request.POST.get('alt_phone', profile.phone)
            address = request.POST.get('alt_address', profile.address)
        else:
            phone = profile.phone if profile.phone else 'Not provided'
            address = f"{profile.address}, {profile.city}" if profile.address else 'Not provided'

        total = 0
        resolved_items = []
        for item in cart:
            try:
                p = Product.objects.get(id=item['pid'])
                qty = item.get('qty', 1)
                sub = float(p.price) * qty
                total += sub
                resolved_items.append((p, qty, item.get('color', ''), item.get('size', ''), p.price))
            except Product.DoesNotExist:
                pass
                
        order = Order.objects.create(
            user=request.user, 
            full_name=request.POST.get('full_name', request.user.first_name), 
            address=address, 
            phone=phone, 
            total_amount=total
        )
        for p, qty, col, sz, price in resolved_items:
            OrderItem.objects.create(
                order=order, 
                product=p, 
                price=price, 
                quantity=qty,
                selected_color=col,
                selected_size=sz
            )
        request.session['cart'] = []
        
        # --- SEND EMAIL CONFIRMATIONS FOR ORDER ---
        customer_email = request.user.email
        customer_name = order.full_name
        
        # 1. Order Confirmation to Customer
        send_mail(
            subject=f"Order Confirmation (#{order.id}) - Belle's Couture",
            message=f"Hi {customer_name},\n\nThank you for your order with Belle's Couture! Your order (#{order.id}) has been successfully placed via Cash on Delivery.\n\nDelivery Address: {order.address}\nTotal Amount: ₱{order.total_amount}\n\nWe will notify you once your order is processed and shipped.\n\nWarm regards,\nBelle's Couture Team",
            from_email=None,
            recipient_list=[customer_email],
            fail_silently=True,
        )
        
        # 2. Order Alert to Artist Admin
        send_mail(
            subject=f"New Product Order Placed (#{order.id}) - {customer_name}",
            message=f"A new order has been placed on Belle's Couture!\n\nCustomer: {customer_name} ({customer_email})\nPhone: {order.phone}\nAddress: {order.address}\nTotal Amount: ₱{order.total_amount}\nPayment Method: Cash on Delivery\n\nPlease check your management system.",
            from_email=None,
            recipient_list=['artist@bellescouture.shop'],
            fail_silently=True,
        )
        # ------------------------------------------

        html = render_template(ORDER_SUCCESS_HTML, {'order': order}, request)
        return HttpResponse(html)
    return HttpResponseRedirect('/cart/')

def orders_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    html = render_template(ORDERS_DASHBOARD_HTML, {'orders': orders, 'cat': 'All', 'brand': 'All', 'q': ''}, request)
    return HttpResponse(html)

def appointments_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    success = None
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        booking = MakeupBooking.objects.create(
            user=request.user, 
            customer_name=request.POST['customer_name'], 
            email=request.POST['email'], 
            phone=request.POST['phone'], 
            service_type=request.POST['service_type'], 
            event_type=request.POST['event_type'], 
            date=request.POST['date'], 
            time=request.POST['time'], 
            address=request.POST['address'], 
            city=request.POST['city'], 
            additional_request=request.POST.get('additional_request', '')
        )
        success = "Appointment booked successfully!"
        
        # Send Booking Confirmation Email to Customer
        send_mail(
            subject=f"Booking Confirmation: {booking.service_type} - Belle's Couture",
            message=f"Hi {booking.customer_name},\n\nYour appointment for {booking.service_type} on {booking.date} at {booking.time} has been received and is currently 'Pending Approval'.\n\nLocation: {booking.address}, {booking.city}\n\nWe will notify you once confirmed!\n\nWarm regards,\nBelle's Couture Team",
            from_email=None,
            recipient_list=[booking.email],
            fail_silently=True,
        )
        
        # Send Alert Email to Artist Admin
        send_mail(
            subject=f"New Makeup Reservation: {booking.customer_name}",
            message=f"A new booking has been placed!\n\nClient: {booking.customer_name}\nService: {booking.service_type}\nDate: {booking.date} ({booking.time})\nCity: {booking.city}\n\nLog in to your Artist Admin Hub to review and accept this reservation.",
            from_email=None,
            recipient_list=['artist@bellescouture.shop'],
            fail_silently=True,
        )

    bookings = MakeupBooking.objects.filter(user=request.user).order_by('-created_at')
    from datetime import date
    today = date.today().isoformat()
    html = render_template(APPOINTMENT_HTML, {'bookings': bookings, 'success': success, 'today': today, 'cat': 'All', 'brand': 'All', 'q': ''}, request)
    return HttpResponse(html)

def artist_admin_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    bookings = MakeupBooking.objects.all().order_by('-created_at')
    html = render_template(ARTIST_ADMIN_HTML, {'bookings': bookings, 'cat': 'All', 'brand': 'All', 'q': ''}, request)
    return HttpResponse(html)

def artist_admin_status(request, bid, status):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    try:
        b = MakeupBooking.objects.get(id=bid)
        b.status = status
        if status == 'Cancelled':
            b.cancelled_at = timezone.now()
        b.save()
        
        # Notify Customer of Status Update (e.g., Accepted, Completed, Cancelled)
        send_mail(
            subject=f"Update on your Makeup Booking (#{b.id}) - {status}",
            message=f"Hi {b.customer_name},\n\nYour appointment status for {b.service_type} on {b.date} has been updated to: {status}.\n\nThank you for choosing Belle's Couture!",
            from_email=None,
            recipient_list=[b.email],
            fail_silently=True,
        )
    except:
        pass
    return HttpResponseRedirect('/artist-admin/')

def register_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            u = User.objects.create_user(username=cd['email'], email=cd['email'], password=cd['password'], first_name=cd['full_name'])
            UserProfile.objects.create(user=u)
            
            # Send Registration Welcome Email
            send_mail(
                subject="Welcome to Belle's Couture!",
                message=f"Hi {cd['full_name']},\n\nThank you for creating an account with Belle's Couture. Explore our luxury beauty collection and book professional makeup artists anytime!\n\nWarm regards,\nBelle's Couture Team",
                from_email=None,
                recipient_list=[cd['email']],
                fail_silently=True,
            )
            return HttpResponseRedirect('/login/?created=1')
    else:
        form = RegisterForm()
    html = render_template(AUTH_HTML, {'form': form, 'title': 'Create Account', 'button': 'Register', 'footer': 'Already have account? <a href="/login/">Login</a>'}, request)
    return HttpResponse(html)

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    success_msg = None
    if request.GET.get('created') == '1':
        success_msg = "You successfully registered, please login now!"
    elif request.GET.get('reset') == '1':
        success_msg = "Password reset successfully! Please login with your new password."
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            u = User.objects.get(email__iexact=form.cleaned_data['email'])
            login(request, u)
            UserProfile.objects.get_or_create(user=u)
            return HttpResponseRedirect('/')
    else:
        form = LoginForm()
    html = render_template(AUTH_HTML, {'form': form, 'title': 'Welcome Back', 'button': 'Login', 'footer': 'No account? <a href="/register/">Register</a> | <a href="/forgot-password/">Forgot Password?</a>', 'success_msg': success_msg}, request)
    return HttpResponse(html)

def forgot_password_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    success_msg = None
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email__iexact=email)
            token_str = str(uuid.uuid4())
            PasswordResetToken.objects.filter(user=user).delete()
            PasswordResetToken.objects.create(user=user, token=token_str)
            
            # Construct absolute reset link with your domain
            reset_link = f"https://bellescouture.shop/reset-password/{token_str}/"
            
            # Send Password Reset Email via Hostinger SMTP
            send_mail(
                subject="Password Reset Request - Belle's Couture",
                message=f"Hello,\n\nYou requested a password reset for your Belle's Couture account. Click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, please ignore this email.\n\nBest regards,\nBelle's Couture",
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )
            success_msg = "Password reset instructions have been sent to your email address."
    else:
        form = ForgotPasswordForm()
    html = render_template(AUTH_HTML, {'form': form, 'title': 'Recover Password', 'button': 'Send Reset Link', 'footer': 'Remembered your password? <a href="/login/">Login</a>', 'success_msg': success_msg}, request)
    return HttpResponse(html)

def reset_password_view(request, token):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    try:
        reset_obj = PasswordResetToken.objects.get(token=token)
        # Check token expiration (e.g., 2 hours)
        if timezone.now() - reset_obj.created_at > timedelta(hours=2):
            reset_obj.delete()
            return HttpResponse("Reset link has expired. <a href='/forgot-password/'>Request a new one</a>")
    except PasswordResetToken.DoesNotExist:
        return HttpResponse("Invalid or expired password reset link. <a href='/forgot-password/'>Request a new one</a>")

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = reset_obj.user
            user.set_password(form.cleaned_data['password'])
            user.save()
            reset_obj.delete()
            return HttpResponseRedirect('/login/?reset=1')
    else:
        form = ResetPasswordForm()
    html = render_template(AUTH_HTML, {'form': form, 'title': 'Set New Password', 'button': 'Update Password', 'footer': '', 'success_msg': None}, request)
    return HttpResponse(html)

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')

def cancel_order(request, oid):
    try:
        o = Order.objects.get(id=oid, user=request.user)
        o.status = 'Cancelled'
        o.cancelled_at = timezone.now()
        o.save()
    except:
        pass
    return HttpResponseRedirect('/orders/')

def delete_order(request, oid):
    try:
        o = Order.objects.get(id=oid, user=request.user)
        if o.status == 'Cancelled':
            o.delete()
    except:
        pass
    return HttpResponseRedirect('/orders/')

def cancel_booking(request, bid):
    try:
        b = MakeupBooking.objects.get(id=bid, user=request.user)
        b.status = 'Cancelled'
        b.cancelled_at = timezone.now()
        b.save()
        
        # Send Cancellation Email to Customer
        send_mail(
            subject=f"Booking Cancelled (#{b.id}) - Belle's Couture",
            message=f"Hi {b.customer_name},\n\nYour booking for {b.service_type} scheduled on {b.date} has been successfully cancelled.\n\nWe hope to serve you next time!",
            from_email=None,
            recipient_list=[b.email],
            fail_silently=True,
        )
    except:
        pass
    return HttpResponseRedirect('/appointments/')

def delete_booking(request, bid):
    try:
        b = MakeupBooking.objects.get(id=bid, user=request.user)
        if b.status == 'Cancelled':
            b.delete()
    except:
        pass
    return HttpResponseRedirect('/appointments/')

urlpatterns = [
    path('', home),
    path('product/<int:pid>/', product_detail),
    path('profile/', profile_view),
    path('register/', register_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('forgot-password/', forgot_password_view),
    path('reset-password/<str:token>/', reset_password_view),
    path('cart/', cart_view),
    path('add-to-cart/<int:pid>/', add_to_cart),
    path('remove/<int:index>/', remove_from_cart),
    path('checkout/', checkout),
    path('orders/', orders_view),
    path('appointments/', appointments_view),
    path('artist-admin/', artist_admin_view),
    path('artist-admin/status/<int:bid>/<str:status>/', artist_admin_status),
    path('cancel-order/<int:oid>/', cancel_order),
    path('delete-order/<int:oid>/', delete_order),
    path('cancel-booking/<int:bid>/', cancel_booking),
    path('delete-booking/<int:bid>/', delete_booking),
]

if __name__ == '__main__':
    from django.db import connection
    call_command('migrate', '--run-syncdb', verbosity=0)
    with connection.schema_editor() as schema_editor:
        try: schema_editor.create_model(Product)
        except: pass
        try: schema_editor.create_model(UserProfile)
        except: pass
        try: schema_editor.create_model(PasswordResetToken)
        except: pass
        try: schema_editor.create_model(MakeupBooking)
        except: pass
        try: schema_editor.create_model(Order)
        except: pass
        try: schema_editor.create_model(OrderItem)
        except: pass
    seed()
    if not User.objects.filter(is_staff=True).exists():
        artist_user = User.objects.create_superuser('artist@bellescouture.shop', 'artist@bellescouture.shop', 'admin123')
        artist_user.first_name = "Lead Makeup Artist"
        artist_user.save()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

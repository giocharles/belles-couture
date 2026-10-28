import os
import sys
import uuid
import json
from datetime import timedelta, datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

MANILA_TZ = ZoneInfo("Asia/Manila")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='belles-final-luxury-2028',
        ROOT_URLCONF='__main__',
        ALLOWED_HOSTS = ['*'],
        CSRF_TRUSTED_ORIGINS = ['https://bellescouture.shop', 'https://www.bellescouture.shop', 'https://belles-couture.onrender.com'],
        TIME_ZONE = 'Asia/Manila',
        USE_TZ = True,
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
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
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
    decline_reason = models.TextField(blank=True, default="")
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
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Confirm Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        if c.get('password')!=c.get('confirm_password'):
            self.add_error('confirm_password',"Passwords don't match")
        if c.get('email') and User.objects.filter(email__iexact=c.get('email')).exists():
            self.add_error('email',"Account already exists")
        return c

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
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
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'New Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Confirm New Password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
    def clean(self):
        c=super().clean()
        if c.get('password') != c.get('confirm_password'):
            self.add_error('confirm_password', "Passwords don't match")
        return c

class UserProfileForm(forms.Form):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control profile-input','readonly':'readonly','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control profile-input','readonly':'readonly','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control profile-input','readonly':'readonly','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control profile-input','readonly':'readonly','rows':3,'style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control profile-input','readonly':'readonly','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-radius:10px; padding:10px 14px;'}))
    current_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Required only if changing password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class':'form-control password-input','placeholder':'Leave blank to keep current password','style':'background:#FAF7F2; border:1px solid #DFD5C6; border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:0; border-bottom-right-radius:0; padding:10px 14px;'}))

# --- SEED PRODUCTS ---
def seed():
    Product.objects.all().delete()
    raw_items = [
        # Careline
        ("Careline Oil Control Face Powder", 185, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRToFG01ZZzykS64u7tMmrgtfRAT-eiWm1X1LzrSGMz-Q&s=10", "Fair, Natural Beige, Warm Honey, Deep Tan", "10g"),
        ("Careline Best Brow Pencil", 175, "Brows", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyq2aOd21QQwURDCt31ioJQoFHVoyRjQ5Wvy1yqHJdVA&s", "Gray Brown, Taupe, Natural Black", "Standard"),
        ("Careline Graph-Ink Liner", 220, "Eyes", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS3kN6feINCOdfZII_JPE3picoegGuJI-dMpVhFHeJWf3j_C6lS6m66Iio&s", "Super Black", "3ml"),
        ("Careline Jelly Tint Lip & Cheek", 150, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6-avXvd7TTMB-p8zx76dlq6m8MmYft2O_JNDKObuKTA&s", "Marshmallow, Just Red, Pink Pout, Berry Glaze", "15ml"),
        ("Careline Acne Spot Concealer", 210, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTyQQit2vqWPsCQnIKJoDamuNeMFxTS3dK7bWGMMIgTbQ&s=10", "Fair Ivory, Light Beige, Warm Honey, Deep Tan", "6ml"),
        ("Careline Strobe Stick Highlighter", 230, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQA-1d7pNbkd2PXgOuTYHmyI8YY5m4MZAqMwox9OIR1eQ&s=10", "Champagne Gold, Rose Glow, Bronze Shimmer", "6g"),
        ("Careline Multi-Use Palette", 350, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSY32SAtYgi0Tnzq4_scR0wf3xUL5t50l7qYtpnQoq5Jg&s=10", "Universal Glow", "12g"),
        ("Careline Scented Lip Gloss", 195, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQztVYpYnkaKDzXe5Jb_zlFT4JnL21PtI2Ha6_BHbi-Bg&s=10", "Strawberry Crush, Vanilla Sparkle, Bubblegum Gloss", "4ml"),
        ("Careline Sponge", 140, "Tools", "Careline", "https://encrypted-tbn2.gstatic.com/shopping?q=tbn:ANd9GcQ2OqiQC1SxcGHJCGuR6NsrzrUPVJ5vkyahBhkF1AQz-9aW9wEgIZ1bjpxLfyUmlrbzYdlzocHhRwa0qKoe4yo7tmZ1SzhP6A", "Standard", "2pcs Set"),
        ("Careline Waterproof Mascara", 250, "Eyes", "Careline", "https://theskincarelibrary.com/cdn/shop/files/CarelineSkinnyMascara.jpg?v=1730710406", "Jet Black", "8ml"),
        ("Careline Matte Lipstick", 210, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShf-4d1KXE2LnZSmwljOegCJc9UB34fJutiGGlSc5QyCwUb3ZMdg84RWs&s=10", "Toast of New York, Cherry Bomb, Vintage Nude, Mauve Mood", "3.8g"),
        ("Careline Sunkissed Bronzer", 280, "Face", "Careline", "https://cdn.salla.sa/aeogjR/9d6242a0-333f-4830-b2a6-5499eb97dcd8-500x500-UUnmvhgxvBf3LOdrhSkhFyWi127VpRDfIDf1MxgC.jpg", "Light Bronze, Warm Tan, Deep Espresso", "7g"),
        ("Careline Everyday BB Cream", 240, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHMOT4PcOHnmUcqnhrsp97dxgF4zYaKyLnku4cEnmB5A&s=10", "Fair Ivory, Natural Beige, Warm Honey, Rich Tan", "30ml"),
        ("Careline Go Big Mascara", 260, "Eyes", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRyS9az9YBToxyt9PscFgsU10gAVVokEvi85puE2AAYwg&s=10", "Ultra Black", "9ml"),
        ("Careline Brow Gel Clear", 180, "Brows", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRb53JtZ_kzff3KuVJ-x04AHRN4OQ75QX9uEuEPR7xA0w&s=10", "Clear", "5ml"),
        ("Careline Velvet Tint", 190, "Lips", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqFgm_kiVSKLQmzZQGzSw8ATcGfCQaJXqRsJBrTxKybA&s=10", "Rose Petal, Berry Smooth, Brick Red, Nude Peach", "4ml"),
        ("Careline Pressed Powder Compact", 200, "Face", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTWpa7sfrlhEhZJPI1nR3VA6CIk-pbGbgikcco7HdwLog&s=10", "Fair Ivory, Natural Beige, Warm Honey, Golden Tan", "10g"),
        ("Careline Sparkle Glitter Liner", 210, "Eyes", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQ20zspW6cG1BvVMkm-XNpDgSN2VjqhxCFGjZTQpHHrg&s=10", "Silver Sparkle, Gold Dust", "3ml"),
        ("Careline Makeup Remover Wipes", 120, "Skincare", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCIuQwCLnOPMaCar1K-AMJp2J7A6ccGq5WvjWhPeIVkw&s=10", "Standard", "30 sheets"),
        ("Careline Setting Mist", 250, "Setting", "Careline", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRxb2TXn4MyC9eIH7I1uCA35kWsnUmHMSbwAOisQoGYeQ&s=10", "Standard", "60ml"),
        
        # Dazzle Me
        ("Dazzle Me Ink-Liner Eyeliner", 189, "Eyes", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQop2Dpceo8c3bu4yCpTxoTDppz28TNtZpqWajBIETFvA&s=10", "Super Black", "1ml"),
        ("Dazzle Me Velvet Matte Lip Cream", 159, "Lips", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTK0viq3XO3iSBp9JjGlEfIRETR81-mQib-IdYQrI5rqg&s=10", "Bite Size, Apple Pie, Velvet Rose, Sunset Coral", "3.5g"),
        ("Dazzle Me Get a Grip Makeup Primer", 269, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfhrSfgO56X4MAZex4mIDeT3y5fTLB8SQAUDtESCv92A&s=10", "Standard", "25ml"),
        ("Dazzle Me Sweet Girl Blush", 179, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWqIPJbTPhVxLyxw9TcZc91nLwQ7DGA9pdxzokJu72lw&s=10", "Mellow Peach, Daydream Pink, Rosy Glow, Sunset Coral", "4g"),
        ("Dazzle Me Holy Moly Eyeshadow Palette", 299, "Eyes", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHEjiYpRFSg4TI_SMf-Vxcr0RY0V-_SCv-3WMrnmpHlw&s=10", "Sunset Glow, Earth Neutrals, Berry Glam", "9-Color"),
        ("Dazzle Me Better Than Filter Loose Powder", 219, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmGCxQ7t-adIXSUnYuGY0zSezKIIpKGcVXQlgPsMCVaw&s=10", "Fair Translucent, Natural Beige, Warm Honey, Deep Tan", "10g"),
        ("Dazzle Me Mist Me Setting Spray", 199, "Setting", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRVqG7s_U6iVF3gZmXJL4wAJkk1eExsKi3Tl3qbouzgew&s=10", "Standard", "60ml"),
        ("Dazzle Me Brow-To-Go Pencil", 149, "Brows", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjWGZ5-U0jhu73bKCKi7YxepDAv-oAzv7Wggm8luNuDA&s=10", "Natural Brown, Dark Ash, Soft Black", "0.3g"),
        ("Dazzle Me SOS Lip Balm", 139, "Lips", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ7Mw75Dl7xoAtgjS5GWdD4LNIU-JCQpsI4buWhxr7wUw&s=10", "Honey Nourish, Rose Tint, Berry Shine", "4g"),
        ("Dazzle Me Juicy Punch Tint", 169, "Lips", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSxbJdGF8y3QXxgx4FmGBxqmzh1jmk9GKUYllKBfm4bFw&s=10", "Cherry Crush, Peach Punch, Watermelon Pop, Berry Fizz", "4ml"),
        ("Dazzle Me Joyful Glow Highlighter", 210, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRe2ynib6NGOLAqcrcpaHZx020fzjiuWadIddshVt3Njg&s=10", "Champagne Glow, Rose Gold Shimmer, Bronze Beam", "5g"),
        ("Dazzle Me Constellation Eyeshadow", 320, "Eyes", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSidhMb3hTk7wU3UCgjbtJKDoEmouwPgrUvX57ikWas-Q&s=10", "Starry Night, Galaxy Glow", "10g"),
        ("Dazzle Me Daily Skin Tint", 280, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRumLgqmWGqydIPsQ1SMRo7GcBiaXpz_nj50oHFjboYKQ&s=10", "Fair Ivory, Light Beige, Warm Honey, Deep Tan", "30ml"),
        ("Dazzle Me Mousse Lip Cream", 170, "Lips", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRK1z_mGU5PtVDInsKoDI5-8pDhiso89IWrtQaLBd9VEA&s=10", "Coral Mousse, Velvet Nude, Berry Cloud, Cocoa Kiss", "3.5g"),
        ("Dazzle Me Soft Blender Puff", 99, "Tools", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMRMTC110RvzX3XQNByENsCjl9IHd6mkE13QLG4zyknA&s=10", "Standard", "1pc"),
        ("Dazzle Me Super Lash Mascara", 230, "Eyes", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSC4faGGmRLIC80foLsnEhk8aMBzcqAW8wocopdfgpWLg&s=10", "Jet Black", "8ml"),
        ("Dazzle Me Poreless Primer", 290, "Face", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjRXHaJ7-wQ7fVFa6b8NjA4R9s52KpbMCRSOg8Spwssg&s=10", "Standard", "25ml"),
        ("Dazzle Me Quick Dry Brow Gel", 160, "Brows", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFtH33aQNpxWqUZ3y8-qv9b-yioKjlKwNkbMTyjotstQ&s=10", "Clear, Brown Tint, Dark Ash", "4ml"),
        ("Dazzle Me Sugar Lip Scrub", 150, "Lips", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTCYYWL8f4Jk9slQpLybTrpPE9BWmo_qIyPL70Gh0QRjg&s=10", "Vanilla Sugar, Honey Berry, Mint Chocolate", "15g"),
        ("Dazzle Me Hydrating Facial Mist", 180, "Skincare", "Dazzle Me", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLOjf7QjWj3ZnfZ2l7dQHYOKOWdd_D4oVxDNMovXBDsg&s=10", "Standard", "100ml"),
        
        # O TWO O
        ("O.TWO.O Golden Glow Liquid Highlighter", 349, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQczU8DJPlUBhmfuCpV4gaWHDeCDgNjkEMmaLZBxEvaiA&s=10", "Champagne Gold, Rose Gold, Bronze Glow", "15ml"),
        ("O.TWO.O Matte Liquid Lipstick Set", 399, "Lips", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQuVtrvWG3NP3rIW6i7w_V44G9IqeAPVxjHL70ezmlEQg&s=10", "Nude Palette, Red Carpet, Berry Romance, Pink Paradise", "3pcs Set"),
        ("O.TWO.O Full Coverage Liquid Foundation", 450, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRcXl9kxFrXtV5Da6TG-dLps_rsXFNLdYYd1Ql6L9xFYw&s", "Fair Ivory, Natural Beige, Warm Honey, Deep Espresso", "30ml"),
        ("O.TWO.O Waterproof Silk Eyeliner Pencil", 199, "Eyes", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwzPjAITtoSGNfEUQy-i6UNm23FwAAtojOqYu0Rag2_Q&s=10", "Intense Black, Espresso Brown", "1.2g"),
        ("O.TWO.O 4-in-1 Eyebrow Pen", 280, "Brows", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS5DAnI9cpu26kDmFfYaPTqBy7q4GPQ4QKHdxhVgwmKWw&s=10", "Dark Brown, Natural Ash, Soft Black", "Standard"),
        ("O.TWO.O Dual-End Sculpt Contour Stick", 320, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSxV3UG8c9C4tYGsyGoMUxcT5Z77kT6boTN027n_0wOaA&s=10", "Light Contour, Medium Sculpt, Deep Bronze", "4g"),
        ("O.TWO.O Silk Mascara Fiber Lengthening", 299, "Eyes", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXNZCz4SSiZFEAMcnhPB2L2ciMKPRgORZhA7S6HhpWDQ&s=10", "Jet Black", "10ml"),
        ("O.TWO.O Velvet Powder Blush", 250, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTzRQS3JM4Iy3GjwgujksGIq-lGCXhaWLgQiWFjTD4vEQ&s=10", "Rose Petal, Coral Crush, Peach Nectar, Berry Bloom", "5g"),
        ("O.TWO.O Pore Minimizing Primer", 380, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR05lpxTF1WdL7Wx7URRmy-gmWB04Dd5ASWRM6-GrDWsw&s=10", "Standard", "30ml"),
        ("O.TWO.O Makeup Setting Spray Oil Control", 350, "Setting", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBnC7VQmW7zPGpXhzF4cKBhJEW4Vcfy2ifqjSUkJeIzA&s=10", "Standard", "100ml"),
        ("O.TWO.O Matte Pressed Powder", 299, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRxO1ugn4PQ65hajh2WBE0a6H0wvDa8ISL2yyPdeH_y1g&s=10", "Natural Ivory, Warm Beige, Deep Tan, Golden Sand", "10g"),
        ("O.TWO.O Glitter Liquid Eyeshadow", 249, "Eyes", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT-IxaQyFjIdExAZ_lolXyAyzxxVDjNo78dROi6mONUBw&s", "Rose Gold Shimmer, Diamond Silver, Champagne Sparkle", "3g"),
        ("O.TWO.O Longwear Lip Gloss", 220, "Lips", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTs9MTEEqvgfmfaR6ZGQF6CXZDRg7iZqJHeN2s8wj9Z-g&s=10", "Clear Glass, Pink Sparkle, Nude Glaze, Berry Shine", "4ml"),
        ("O.TWO.O Ultra Fine Brow Pencil", 180, "Brows", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSkv06PpUQJFlibGJ5LLamaJqyhu0xsCAXsfwN5Zi9Qzg&s=10", "Dark Gray, Natural Brown, Soft Black", "0.1g"),
        ("O.TWO.O Face Concealer Palette", 350, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQpwRIbJj955qLwnEA8q8WOFyIerQTtumI90yeVtyHa6g&s=10", "Light Correctors, Medium Coverage, Deep Conceal", "15g"),
        ("O.TWO.O Makeup Brush Set", 699, "Tools", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS3RnIvkjYBDuJ8DH_QTEzEV0gWjdDXKlNWDyJdNjBi4A&s=10", "Standard", "12pcs Set"),
        ("O.TWO.O Tinted Lip Oil", 260, "Lips", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrsn_qQOIl55rWOAEwcipfK_xayr8IFDDFPtTQ1EcUTg&s=10", "Honey Tint, Cherry Glaze, Rose Infusion, Mint Glow", "5ml"),
        ("O.TWO.O Volume Curling Mascara", 310, "Eyes", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTkqX8EFRMrcKvbPbwEizCmVg2EzgCHnGghJ80wDOtbBw&s=10", "Jet Black", "8ml"),
        ("O.TWO.O Makeup Remover Cleansing Balm", 390, "Skincare", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqhu1Lx0KqXdpFgG2dSXOtBx9THIjIoeAiagc2GM6UOQ&s=10", "Standard", "100g"),
        ("O.TWO.O Matte Liquid Foundation", 420, "Face", "O TWO O", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzOgqVaoIZ7jyZ5E_yFcJMycpJ3zYt57BOt2hVp_cotQ&s=10", "Fair Ivory, Warm Beige, Golden Tan, Deep Espresso", "30ml"),
        
        # Vice Cosmetics
        ("Vice Co. Gandallier Eyebrow Pen", 245, "Brows", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQPzW9ERbS-pNn6bgpuqeFj0NkprWwJsUbIipPT2pEB-g&s=10", "Ash Brown, Natural Brown, Soft Black", "0.5g"),
        ("Vice Co. Velvet Lip Credible", 295, "Lips", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWoQdpEyawGA2e8g8c5PD6Jb8tzAioRGLHXiI6Swwh4g&s=10", "Kroma, Pilya, Ganda, Pak!, Aura", "4g"),
        ("Vice Co. Aura Blush Collection", 225, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVRu_8y0o-BvkW5zjPzpWx22ODFM5ZVakVD4F8HsPQ8A&s=10", "Shalala, Flawless, Dyosa, Keri", "5g"),
        ("Vice Co. Endle-Slay Setting Spray", 345, "Setting", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTgJ2wCvBjACNUKQxlmH8205rSpsAI0Js9gx8rGH_hmyA&s=10", "Standard", "100ml"),
        ("Vice Co. Phenomenal Liquid Lipstick", 295, "Lips", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShA1ffpt7U4fvoKE13yWwgNLyTfcFKmPBIGCULdwl-pQ&s=10", "Tunay, Truth, Ganda Lang, Rampa, Bongga", "3.8g"),
        ("Vice Co. Mood Proof Eyeliner", 220, "Eyes", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGjWYJGxpnhWRf_Pa7R3IykKktk6Nd2J2By3o-NkQsGg&s=10", "Jet Black", "1.5ml"),
        ("Vice Co. Zero Tinted Lip Oil", 245, "Lips", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT7vYk0w0lZ_FVhhYk-sGHqcXlAuxzGinAhhZ7gqOUPGA&s=10", "Clear Glass, Peach Glow, Rose Tint, Berry Shine", "4ml"),
        ("Vice Co. Perfect Cover Concealer", 275, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR2pvmODqF85L1seWE9IV4IE1HjfnfyudaAKzppwLTIPQ&s=10", "Fair, Light Beige, Medium Warm, Deep Tan", "8g"),
        ("Vice Co. Aura Contour & Highlight", 320, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCsyMTlvU67qzfrHPZwDaBCPTKTyTyTveI2SI9FXsCmA&s=10", "Bronze/Pearl Duo, Warm Contour/Champagne Highlight", "8g"),
        ("Vice Co. Soft Focus Pressed Powder", 295, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRoXtyJT50LiT-0o8N5RXpbz6YSyH9o_cRqkh0E2MpPTA&s=10", "Light Beige, Natural Warm, Golden Sand, Deep Tan", "10g"),
        ("Vice Co. Grand Volumizing Mascara", 310, "Eyes", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpsK1-z1wamN39AtqLyL5kxGj-2HrrLeyoQl6A7MxiFg&s=10", "Intense Black", "8ml"),
        ("Vice Co. Lip Liner Pencil", 180, "Lips", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLiu8ZjIHKuJcPr4JSo-8FvDZcezJZcu0OTdiiE34oCw&s=10", "Nude Craze, Classic Red, Mauve Magic, Brown Sugar", "1.2g"),
        ("Vice Co. Dewy Finish Skin Tint", 350, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ16iGn1H6_X_c_3J1QsT_8NjTOEyoZ1IPmt0RD9iTvfA&s=10", "Fair, Light Beige, Medium Warm, Golden Tan, Deep Espresso", "30ml"),
        ("Vice Co. Aura Illuminating Drops", 330, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSeYsZUBSrP-pMqnPYJ4Pu4hV5BywgACbtppPqGpSO_Yw&s=10", "Pearl Glow, Champagne Shimmer, Rose Gold", "15ml"),
        ("Vice Co. Eyebrow Soap Styler", 210, "Brows", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLEO1T6bimJ4NLKvlG3hzqbzn3ixnXh6KFcgAl0-FyOw&s=10", "Clear", "15g"),
        ("Vice Co. Superstay Matte Lipstick", 295, "Lips", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTNKPwUxrAyhayejZG0_f7105CdloTZSuJm8tdWtEPVvQ&s=10", "Pout, Fierce, Pak, Bongga, Charot", "4g"),
        ("Vice Co. Pore Blurring Primer", 340, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQPCUQKlO0iEdVV7cD2kkO_wRFcY0kAeR4hGXuP6x619w&s=10", "Standard", "25ml"),
        ("Vice Co. Everyday Makeup Sponge", 150, "Tools", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQulBRkFMBIiNyoRmYt0ZUVWuNjWt1_Fq_2LTO3g9ijzA&s=10", "Standard", "1pc"),
        ("Vice Co. Loose HD Setting Powder", 320, "Face", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRwWpB5DNSz0XoS4v3XCiH50wn4E53BXhY192EU-7Zd6g&s=10", "Translucent, Fair Glow, Warm Beige", "12g"),
        ("Vice Co. Colour Palette Eyeshadow", 450, "Eyes", "Vice Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTNDxk5kYJvzQ0fpkk1-8c46nK1DMPiV8XLT1PmJooHBg&s=10", "Gala Mix, Everyday Nudes, Festival Glam", "8-Color"),
        
        # BLK
        ("BLK Cosmetics Universal Lip Tint", 349, "Lips", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQCGWOT3abAbtOhwkZobrLPyvIwtuN5LYMIFsT5pWyvlw&s=10", "All Day, Pink Sunday, Berry Vintage, Coral Sunset", "10ml"),
        ("BLK Cosmetics Daydream Airy Matte Tint", 399, "Lips", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYYdVxaK0ZJLhmbYgkrk_XIOWp0C1raMRMwC3nTkkSzQ&s=10", "Chic, Muse, Velvet, Sassy, Dreamy", "4g"),
        ("BLK Cosmetics All-Day Liquid Foundation", 699, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTZaXo-WVHOXcAgy2wajSRRRL6W1eWXSnezXyeBbjwfAw&s=10", "Vanilla, Warm Beige, Natural Tan, Deep Golden", "30ml"),
        ("BLK Cosmetics Creamy All-Over Paint", 449, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_4EoGCHOzimJWtW_hvK88AnkwKtFXLBtUO8Pd1tuWRw&s=10", "Beach, Sunkissed, Rose Petal, Peachy Glow", "5g"),
        ("BLK Cosmetics Sculpt & Glow Contour Palette", 599, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHxtDgmcRh6ff7gRKVmBQHuiwxfRnFCEHlXt7J3rwyfw&s=10", "Warm Duo, Cool Duo", "12g"),
        ("BLK Cosmetics Eyebrow Pencil & Brush", 325, "Brows", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQpag7sDS9a3Wrf5bTlw3IWjeei-IuQ1ayveVttno7h6Q&s=10", "Natural Brown, Dark Brown, Soft Black", "Standard"),
        ("BLK Cosmetics Long-Lasting Eyeliner", 369, "Eyes", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVOH3ly7MS3pTX1mMCQnyD2t1EmnSB_HU3KToMqBYbmA&s=10", "Intense Black", "1.2g"),
        ("BLK Cosmetics Face Setting Powder", 499, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6U4vI3y9jtaOxHWFZ3x0brdoXBf4xINIRrtsYzOnqVA&s=10", "Translucent, Fair, Natural Beige", "10g"),
        ("BLK Cosmetics Intense Volume Mascara", 450, "Eyes", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-uztslmoeWtIFn8pYsqPGmrQWHSLEv2MMqT67uFKRZQ&s=10", "Jet Black", "8ml"),
        ("BLK Cosmetics Hydrating Lip Oil", 379, "Lips", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTy2GPZHRWHC4OnVgHbinKm2kB5LE9cBntUXlnpRcMasw&s=10", "Honey Glaze, Rose Shine, Berry Nectar, Clear Dew", "5ml"),
        ("BLK Cosmetics Skin Tint Sun Shield", 499, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgsc2ZwspYqurT3jT5m54OMc2zcM3PJg3i2-r0tUyPAg&s=10", "Light, Natural Beige, Warm Tan, Deep Golden", "30ml"),
        ("BLK Cosmetics Creamy Cheek Paint", 380, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQBCWk2aOGtyHvp4fOR00xCN-A8cISJlM21p0UmfZ7LeQ&s=10", "Rose, Peachy Glow, Sunlit Bronze", "10ml"),
        ("BLK Cosmetics Matte Lipstick Deluxe", 399, "Lips", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyhbQost2G8yQHcQIacXIqItU8fRZtcdzofdOkzRlheg&s=10", "Classic Nude, Retro Red, Vintage Rose, Spice Brown", "3.8g"),
        ("BLK Cosmetics Eyebrow Mascara", 310, "Brows", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQI8NVMtS6UbAbXnjWse4G9vlbhGgwTBzCOTdAsCWCXQ&s=10", "Brown Tint, Dark Ash, Clear", "5ml"),
        ("BLK Cosmetics Full Coverage Concealer", 420, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTyh889BTS_0VnprMLGPM5dhDs5LIp0rJ2911-IXMNAog&s=10", "Fair, Light, Medium Warm, Deep Tan", "8ml"),
        ("BLK Cosmetics Refreshing Setting Spray", 450, "Setting", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAONJnu2yczAhDTnI_PPeXvnJ3z-ja8hZ85-VYLhVipQ&s=10", "Standard", "100ml"),
        ("BLK Cosmetics Mini Eyeshadow Palette", 550, "Eyes", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQf6HrUe7XlQPfCfpvDknXLCO2rkbrLlUPWSzIMu-5lAg&s=10", "Nude Neutrals, Warm Rose, Smokey Glam", "6-Color"),
        ("BLK Cosmetics Double-Ended Brush", 480, "Tools", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4AnZ3Gi_2MjtvwVw7rF-jzTyzON1FvtmAjy-OGNimNQ&s=10", "Standard", "1pc"),
        ("BLK Cosmetics Velvet Lip Butter", 360, "Lips", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGuD_eqobsT26poYof_M-PzqNYVlatuxLHiyPlwXl0jQ&s=10", "Butter Pink, Toffee Nude, Warm Caramel, Cocoa Velvet", "4g"),
        ("BLK Cosmetics Glow Highlighting Stick", 430, "Face", "BLK", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMAb9yKfkDhkIhghhdJdu0LuPGH4F6AsGj-UYvfDERgA&s=10", "Champagne Shimmer, Rose Gold, Bronze Glow", "6g"),
        
        # Ever Bilena
        ("Ever Bilena Matte Matic Lipstick", 220, "Lips", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQP9taeThN-IjAt5koy4QX70VzWB47DVeSXfVxJy21APg&s=10", "Toast of New York, Caramel, Vintage Red, Mauve Matte", "3.5g"),
        ("Ever Bilena Advanced Liquid Concealer", 240, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkPmiaruDmMNVjbN8m0VVgof34U4sdmGXR7m15e35NCw&s=10", "Light Ivory, Medium Beige, Warm Tan, Deep Bronze", "10ml"),
        ("Ever Bilena Direct Universal Eye Pencil", 150, "Eyes", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR18S8PRTv0Q3PoBfP2Ip_XdU8XZ5LuUmNb-MXacqTkMA&s", "Matte Black, Dark Brown", "Standard"),
        ("Ever Bilena Face Palette Blush & Contour", 380, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDgBn1hLywCiBHtMBKvUxTDHjEDezpyFx-H5mQ_8PSOQ&s=10", "Warm Tones, Cool Sculpt Duo", "14g"),
        ("Ever Bilena Scenically Dewy Foundation", 350, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQbC2NJ_szqknWzJCUdN7wSAVAsvkI2kUxpgN9_xNP7iQ&s=10", "Oriental, Natural Beige, Warm Honey, Golden Sand", "30ml"),
        ("Ever Bilena Plus Hya Tinted Serum", 310, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSRcLKYuKaMTuHfBvG9LwatxD8apQIeWRzWophYO9Fnxg&s=10", "Light Tint, Natural Glow, Warm Tan", "20ml"),
        ("Ever Bilena Plus The Over-Acheiver Brow", 230, "Brows", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWkm7Sc829UVJGbNcqKLsOWQd9E7Vawp6IquKn0mNOSw&s=10", "Taupe, Brown, Dark Ash", "Standard"),
        ("Ever Bilena Plus Feature Lengthening Mascara", 290, "Eyes", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqcbsYqTe5T7Rjw4SwPvILyWPBIQSeAZg-_MAt5k4xLw&s=10", "Jet Black", "8ml"),
        ("Ever Bilena Maximum Setting Spray", 320, "Setting", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRKyjUShVb7ocECWEJUJgKOXErhdU8DoO3Jft1F_VXkpw&s=10", "Standard", "80ml"),
        ("Ever Bilena Matte Powder Compact", 210, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6-lgkyvwugw5iOsM5qgWtUzurCxOHguBxLiv94vozKFw8PbR96VF05tA&s=10", "Natural Beige, Medium Warm, Golden Sand, Deep Bronze", "10g"),
        ("Ever Bilena Lip Gloss Crystal", 190, "Lips", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS3edIaXGP4FCMMBfk2_S75FcDozxkAlA7A4380NJTHtQ&s=10", "Clear Crystal, Rose Shimmer, Nude Glaze", "4ml"),
        ("Ever Bilena Eyeshadow Single", 160, "Eyes", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRI6D3ZJfchcUhwOpvA81j50ewEYBlTYobeDBHrLM0GBA&s=10", "Champagne Shimmer, Bronze Glow, Matte Brown", "2g"),
        ("Ever Bilena Lip and Cheek Tint", 175, "Lips", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTcYIvpDUZmLeOeB8F_O3m9GfbJVhkkZD4YaGRI98a5-A&s=10", "Red Red, Orange Crush, Pink Pop, Berry Wine", "15ml"),
        ("Ever Bilena Eyebrow Powder Duo", 210, "Brows", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTzp5EZ1Oy7hq9ckQ0vZNFrqV_lMBcq5obL-YFOqdL3XQ&s=10", "Brown Duo, Ash Duo", "4g"),
        ("Ever Bilena Strobe Cream Highlighter", 250, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRubLTlutptI1YJvhpHHic-darDyVyf1W0Ys4jIZwSL9A&s=10", "Gold Glow, Rose Beam, Champagne Shimmer", "15ml"),
        ("Ever Bilena Pore Refiner Primer", 290, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8IsehUggAAbWthZkPg5B_asAlVFt_NPtk6XyCdkpsEw&s=10", "Standard", "25ml"),
        ("Ever Bilena Color Corrector Stick", 220, "Face", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsvwM3N6BAABqLTwcBEE0g_HTHL1CV3UqZafdDHRTbwA&s=10", "Green Corrector, Peach Corrector, Yellow Brightener", "4g"),
        ("Ever Bilena Precision Liquid Liner", 200, "Eyes", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWy9EoSjYOeZ4RYdQsUibFTXrwY6_QYL_f4Wk50YmFkw&s", "Matte Black", "3ml"),
        ("Ever Bilena Complete Brush Kit", 550, "Tools", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSQQ7cjG0Blm94SG-l73QbjIcYIiy6snRyg1kxvadhg_w&s=10", "Standard", "7pcs Set"),
        ("Ever Bilena Velvet Lipstick", 230, "Lips", "Ever Bilena", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7cT0ytDghTU2tNHVWx50u9sRSFa471VjbfzhIoHcFzA&s", "Soft Pink, Classic Nude, Warm Peach, Berry Velvet", "3.5g"),
        
        # --- GRWM Cosmetics (30 Products) ---
        ("GRWM Cosmetics Radiance Tint Multi-Use Concealer", 380, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQfvKFvIDKI5b0rCGbI-9OWvw0EMBiXjHBHEaJDhjpmhQ&s=10", "Fair 1, Light 2, Medium 3, Warm Tan 4, Deep Espresso", "10ml"),
        ("GRWM Cosmetics Quad Goals Multi-Purpose Palette", 599, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTf_PaH4G4sG4mQyIgFKgxS-_o1HRn3o8j6dAMBxk40HA&s=10", "Universal Warm, Neutral Glow, Cool Glam", "15g"),
        ("GRWM Cosmetics Milk Tint Cream Blush", 349, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuRJIxEioeTdqpxPhNeHwGrp8TNZafiVc9ndoiHbpXng&s=10", "Horchata, Pablo's Latte, Churro, Strawberry Milk, Pomelo", "10ml"),
        ("GRWM Cosmetics Eyebrow Duo Soap & Pomade", 320, "Brows", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_bu6_SGZipmeiiAgkyHH4yQrwwlBpX94mdyEg-Vq3Hg&s", "Clear, Brown Tint", "8g"),
        ("GRWM Cosmetics Loose Setting Powder", 420, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQCsJMWRwS8o9Oe1_nu_uZ8cris-n5oapV_O9me3M6v4g&s=10", "Translucent, Fair Glow, Warm Honey, Deep Tan", "12g"),
        ("GRWM Cosmetics Glow Tint Highlighter", 360, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqFqtr58PSvxMYOcSBoNCcj_3oIqZa4YCs7ZnSXzu9iA&s=10", "Champagne Shimmer, Rose Gold, Bronze Glow", "10ml"),
        ("GRWM Cosmetics Ultimate Setting Spray", 450, "Setting", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVHRm5_I8zmvDGY5xvcd5Tpc5mX4fNS2gmXd5tl96fNg&s", "Standard", "100ml"),
        ("GRWM Cosmetics Lip Trace Lip Liner", 250, "Lips", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQjnl4JVk-0RnXq6lctujueU_VNhEjlH0wIW9MNv7L1TQ&s", "Nude Contour, Rose Brown, Warm Terracotta, Deep Berry", "1.2g"),
        ("GRWM Cosmetics Velvet Matte Lipstick", 380, "Lips", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAtQbmzNBoqE5xHIXpByO55vqqb921efbK_E0RTOm8eA&s=10", "Rosewood, Nude Spice, Terracotta, Vintage Red", "4g"),
        ("GRWM Cosmetics Skin Goals Foundation", 550, "Face", "GRWM Cosmetics", "https://laz-img-sg.alicdn.com/p/6805e500ef21314b4797170d119d9e00.jpg", "Fair 1, Light Beige, Warm Honey, Golden Tan, Deep Espresso", "30ml"),
        ("GRWM Cosmetics Precision Eyeliner", 290, "Eyes", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSCZoWy6C25X7XTX2TWBf0LlQrra59xbol6eSMY5E3FKA&s=10", "Jet Black", "1.5ml"),
        ("GRWM Cosmetics Lash Lift Mascara", 390, "Eyes", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcaG6V_SLwZLSqmL0AzwVWOIXu5PVLIbW84_CpRzI8YA&s", "Intense Black", "8ml"),
        ("GRWM Cosmetics Contour Stick", 399, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZ6Tv-pStKIdEbiTwXOVMSOTOBxsKqdMUGj_xRnKfjbw&s=10", "Cool Bronze, Warm Sculpt, Deep Espresso", "6g"),
        ("GRWM Cosmetics Colour Corrector", 360, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFIhXORjDJb8Sm5vWEQJJtHrbPRxnlwylq_IRpCsUJKg&s", "Peach Corrector, Green Neutralizer, Yellow Brightener", "10ml"),
        ("GRWM Cosmetics Tinted Brow Gel", 310, "Brows", "GRWM Cosmetics", "https://www.grwmcosmetics.com.ph/cdn/shop/files/Maxx_Browlift.jpg?v=1772516530&width=1445", "Natural Brown, Dark Ash, Clear", "5ml"),
        ("GRWM Cosmetics Primer Shield", 480, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQfn8VyN851t7wddM5OKUG6-jpca97YhkfncsefFzpHtQ&s", "Standard", "30ml"),
        ("GRWM Cosmetics Super Gloss Lip Oil", 350, "Lips", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5XryCJvZdc_AcsnIVMXriVLUBC_9lEsJ-x3gFmKovyg&s", "Clear Shine, Honey Glaze, Rose Dew, Berry Shimmer", "5ml"),
        ("GRWM Cosmetics Cream Bronzer", 410, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRM9xvTy2cxoNi2UK60jnTF79uXhXlNwhTTUpx1UycOUA&s=10", "Sunlit Bronze, Warm Contour, Deep Tan", "8g"),
        ("GRWM Cosmetics Eyeshadow Single Shimmer", 220, "Eyes", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTmcILjix6jy_Tt76OQOQsR6KIS-Yua0-T9Y7kSpOvWKg&s=10", "Bronze Glow, Champagne Shimmer, Rose Gold", "2g"),
        ("GRWM Cosmetics Face Mist Dewy", 380, "Setting", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSKc4rfw07sYgPXQ1W8oM3QHys7WzgHkGxhN0HrZgC2AA&s=10", "Standard", "80ml"),
        ("GRWM Cosmetics Dual Fiber Blending Brush", 450, "Tools", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS5uZyOVW9jPkntDJPF6A6aBptDBOkEL98ep31aBaoQGw&s=10", "Standard", "1pc"),
        ("GRWM Cosmetics Brow Stroke Pen", 330, "Brows", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ29sZ_w7MFi_vc40lt9T5oM5UPo77LUQvJ1CLGrBFTQw&s", "Dark Brown, Ash Brown, Soft Black", "0.5g"),
        ("GRWM Cosmetics Pressed Powder Foundation", 480, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4LEI0XZRCqbMo7O4_SxR3T9njsd-ADqA3AVBw4OHEnw&s=10", "Fair, Natural Beige, Warm Honey, Golden Tan, Deep Espresso", "10g"),
        ("GRWM Cosmetics Lip Stain Tint", 340, "Lips", "GRWM Cosmetics", "https://www.grwmcosmetics.com.ph/cdn/shop/files/Ecomm_CushionTint-01_8e585f51-9146-4358-80b0-d5bcd2b88f9b.jpg?v=1779248623&width=1946", "Berry Punch, Cherry Red, Peachy Nude, Rose Petal", "4ml"),
        ("GRWM Cosmetics Under Eye Brightener", 370, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTnzGcX-VgGywUxPKsIIHNF-hrPIWFZKINNeoGiAd0m8A&s=10", "Bright Peach, Golden Amber", "8ml"),
        ("GRWM Cosmetics Lip Plumper", 390, "Lips", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRq1-ZaepZ4HTSv100PDQYjcjXZZJYgD8VzHBz9HllxIw&s", "Clear Gloss, Pink Tint, Nude Shine", "4ml"),
        ("GRWM Cosmetics Liquid Highlighter Drops", 420, "Face", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsuqrHn4mb2oxvfuTLB81vpHLTi0TXOfMlSYKT12kwyg&s=10", "Rose Gold, Champagne Beam, Bronze Glow", "15ml"),
        ("GRWM Cosmetics Hydrating Lip Balm", 290, "Lips", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQeE5_e9Mvf8h_ScycQVzPbKZLLCJ5V1NydEbVbufEn9g&s", "Vanilla Sugar, Honey Butter, Strawberry Mint", "4g"),
        ("GRWM Cosmetics Pro Makeup Sponge", 190, "Tools", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTr1o4swYs556hPW3ki258Kh0OMaWs8PfBlR0l7t4c1Vw&s=10", "Standard", "1pc"),
        ("GRWM Cosmetics Complete Brush Set Pro", 890, "Tools", "GRWM Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQwc9JI0QZsoAl1O1pF1Cg18Sauyc9cfuy9eV_KCTJzzg&s=10", "Standard", "10pcs Set"),

        # --- Issy Cosmetics (30 Products) ---
        ("Issy Active Skin Tint", 499, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6zF6duSJI5vvbMD7CCi-V__iynr6fRPFlBcnwwIaVTA&s=10", "Fair 1, Light 2, Medium 3, Warm Tan 4, Deep Espresso", "30ml"),
        ("Issy True Flex Concealer", 480, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvDk3CUjNGqxBOsq_XFn2iwxxA83v6XladAfrHgTQpoQ&s", "FR1, LT2, MD1, WN2, DP1", "10g"),
        ("Issy Solar Balm Tinted Lip Balm", 399, "Lips", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3wmatwVcQ3YVX2dAwizqt6GgPm6_E1jY-HXJkSIT7hQ&s=10", "Nude Peach, Berry Wine, Rose Petal, Cocoa Gloss", "4g"),
        ("Issy Hydrating Lip Gloss", 349, "Lips", "Issy Cosmetics", "https://storage.skinsort.com/jd2b28ebenmtdjq8slvcyyx536n7", "Glass Shine, Pink Glaze, Nude Shimmer, Berry Sparkle", "4ml"),
        ("Issy Precision Brow Pencil", 320, "Brows", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRwM5rN44HCaALiOGDJb7OMFoSf1xctjAbK6Oys-XSGeQ&s=10", "Taupe, Ash Brown, Dark Brown, Soft Black", "0.2g"),
        ("Issy Brow Refiner Gel", 340, "Brows", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwvbiKEZrV1h1rpwFM9lZhTlQr6NkwNpJ3S7t0IS9bcQ&s=10", "Clear, Brown Tint, Dark Ash", "5ml"),
        ("Issy Cream Blush", 399, "Face", "Issy Cosmetics", "https://pnybeauty.com/cdn/shop/products/CREMEBLUSHSCANDALOPEN.jpg?v=1663601084", "Tutu, Sangria, Flushed, Rosy, Peach Nectar", "5g"),
        ("Issy Cream Highlighter", 399, "Face", "Issy Cosmetics", "https://down-ph.img.susercontent.com/file/ph-11134207-81ztk-me1abser98ubd2", "Pearl Glow, Champagne Shimmer, Bronze Beam", "5g"),
        ("Issy Cream Contour", 399, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTJf1ro8dUQeBeVaeE8zGNUii1OncXeq7Hm6vEIc3cZPw&s=10", "Sculpt Light, Sculpt Medium, Sculpt Deep", "5g"),
        ("Issy Weightless Loose Powder", 499, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqPhRLLwVExH8ozT2w3Iy7YrsBvNOHunHouJMqbfu6Pw&s", "Translucent, Fair Glow, Warm Honey, Deep Tan", "10g"),
        ("Issy Mattifying Primer", 450, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSZ9V9kJZhqAYOviEzugZaERpZYA_zJMkBo8XnwE1GxMw&s=10", "Standard", "25ml"),
        ("Issy Setting Spray Mist", 480, "Setting", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXuG0Gngwuieg5qE4ojt7tcegpruaJ7u6Z8f5RDyUxOw&s=10", "Standard", "80ml"),
        ("Issy Liquid Lip Mousse", 380, "Lips", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9T8gTMKgYEgCkL-e6nALKzV-URAg6k6e71ucLejHSbg&s=10", "Muted Nude, Dusty Rose, Brick Red, Cocoa Mousse", "3.5g"),
        ("Issy Gel Eyeliner Pencil", 299, "Eyes", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHv4S9KDO0tA50h7I-6k4zMXxyAlJ2KxfFxia8ONhonw&s", "Espresso, Jet Black, Deep Brown", "1.2g"),
        ("Issy Lengthening Mascara", 420, "Eyes", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTmBmqf274lyjKBP-0UPpR0unpJUaqz8jxfxhDAVIWz-w&s", "Intense Black", "8ml"),
        ("Issy Eyeshadow Quad Palette", 550, "Eyes", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGjvBravX7M-3ZJHvDeJ38fMxzAN6qGRE9oYTLc2eiUA&s=10", "Neutral Warm, Cool Taupe, Rose Glam", "6g"),
        ("Issy Hydrating Under Eye Corrector", 420, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCYdLgusZOgfd3GBAK0I2_wN8O8CLE-H6qNsTRdPGp1g&s=10", "Peach Corrector, Amber Brightener", "8ml"),
        ("Issy Lip Oil Treatment", 380, "Lips", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQjXq7_CyFxws_6ziwYkn2JKNC381z0PeqBL28AqMrDkA&s=10", "Nourish Clear, Rose Tint, Honey Glaze", "5ml"),
        ("Issy Pressed Powder Compact", 490, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSAnSB5CZC0Hvb9VzWI-lTJMB4LS05cW1jMQgG9D7PtFg&s", "Fair, Natural Beige, Warm Honey, Deep Tan", "9g"),
        ("Issy Brow Pomade", 360, "Brows", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQS6a6WLxAp3i8zS5hYfil7_wtzSeJOalV3ogmIN-IXVw&s=10", "Dark Brown, Ash Brown, Soft Black", "4g"),
        ("Issy Lip Liner Pencil", 280, "Lips", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSRwEdR26281uLavg69GtDrMEWYREhCcqYpSafp09bR3Q&s", "Mauve Nude, Terracotta, Classic Red, Deep Cocoa", "1.2g"),
        ("Issy Makeup Sponge Puff", 180, "Tools", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRXvfxZECi7QukYDclxI1DQoBGMjM6sbEqWVtAPf1z0qA&s", "Standard", "1pc"),
        ("Issy Complexion Blending Brush", 420, "Tools", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAt56YUUcyAqHFeJYBTB0va4Mx-wsS_XKf1vMwC6_STw&s=10", "Standard", "1pc"),
        ("Issy Dewy Skin Mist", 450, "Setting", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-nUTyPwXZfCPbVQndtrsChq14F0xrDlzPppcwovJQzA&s", "Standard", "80ml"),
        ("Issy Liquid Eyeshadow Shimmer", 399, "Eyes", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1qUaoUEqmeEIcyYH65LQ2tW9cnje9HtQdSkUp5Eh3nw&s=10", "Champagne Shimmer, Rose Gold, Bronze Sparkle", "3g"),
        ("Issy Lip Stain Gloss", 390, "Lips", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRgItHOfoCw7wWaEgM1B2sLsFEZFsKGwdcbWHvpsy5Cyw&s", "Cherry Gloss, Peach Glaze, Berry Tint, Nude Shine", "4ml"),
        ("Issy Color Correcting Primer", 460, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTunSJsV2TxOKPw7arWAE9B4ny73XmAhoS--jO2Rz2IYw&s=10", "Green Tone, Peach Tone, Lavender Tone", "30ml"),
        ("Issy Micro Brow Pen", 350, "Brows", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSnyA1NFDiVBjoemQGRI4nKtd1b_7kQc8o9lUiIW5Igrg&s", "Darkest Brown, Ash Brown, Natural Black", "0.4g"),
        ("Issy Highlighter Powder", 450, "Face", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTRZDrOBog3ex8GCACLaHUDVn_CNi90DWO9egItwOGCJA&s", "Golden Glow, Champagne Shimmer, Rose Beam", "7g"),
        ("Issy Ultimate Pro Brush Set", 990, "Tools", "Issy Cosmetics", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQY0MX5GrATJ9kO8js--44IJUWZEwWj0AMOX4b04GBBpw&s", "Standard", "12pcs Set"),

        # --- Lucky Beauty (20 Products) ---
        ("Lucky Beauty Dewy Serum Foundation", 580, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQD1ajxTep7POiANgAaNOUqEaNHrS8JBhaL4V3lezD6OA&s", "Fair Ivory, Natural Beige, Warm Honey, Golden Tan, Deep Espresso", "30ml"),
        ("Lucky Beauty Tinted Lip Serum", 345, "Lips", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_Fw9ydgEAVzZpmjUaXYUl0XDjToV7lzpMtzTdxv51Aw&s", "Nude Glaze, Mauve Glow, Berry Infusion, Peach Shine", "4ml"),
        ("Lucky Beauty Liquid Blush", 360, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQASBYYKSkqsOqjcgH_BcNxbhJhw_vHCczodLHfRQi3kA&s=10", "Peachy Glow, Rose Petal, Sunlit Coral, Berry Flush", "10ml"),
        ("Lucky Beauty Cloud Matte Lipstick", 380, "Lips", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT-BZnFQlWaBkseya5J13hVhSXuNYfHj9INstBuBoFV0w&s=10", "Dainty, Grace, Muse, Fierce Red, Velvet Nude", "3.8g"),
        ("Lucky Beauty Brow Laminator", 320, "Brows", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTopG3db67Y-dZ20y1vfSdcKfg-L3vCxGXPvy5-uQsy_Q&s=10", "Clear, Brown Tint", "6g"),
        ("Lucky Beauty Setting Powder Translucent", 420, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLLd9QuGIOyk_sYe35-P05l5ttZPFnV4M1UYsX3A5GkQ&s", "Translucent, Fair Glow, Warm Honey", "10g"),
        ("Lucky Beauty Glow Highlighter", 390, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQE_gO0cwt3mfXr0p29_-7kIfRSiKjMBGP-v0uJt3_VdQ&s=10", "Champagne Beam, Rose Gold, Bronze Shimmer", "6g"),
        ("Lucky Beauty Hydrating Setting Mist", 410, "Setting", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQBqhPhMt_oioZnx2o7qJJV3v8LxpejBhxXdaMCVied_g&s=10", "Standard", "80ml"),
        ("Lucky Beauty Volumizing Mascara", 440, "Eyes", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRupE5-Bvrhi06SI6U1LWCcqYXAYBK1PkI9YOIbzHs9ng&s", "Jet Black", "8ml"),
        ("Lucky Beauty Precision Eyeliner", 310, "Eyes", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTkY0EEE2Oas7VOG-p3BWRYyvhtqBvsLNOWPoe_cK5GgQ&s=10", "Intense Black", "1.2ml"),
        ("Lucky Beauty Cream Contour Stick", 420, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzZiG-U1VukBQJBSmugEvplqgb2jhNTrfL1ePj2FJ6xw&s", "Soft Bronze, Warm Sculpt, Deep Espresso", "6g"),
        ("Lucky Beauty Concealer Cream", 390, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSBbLVcTs6gzM6cGywhgHUvjKdW3kqW07bbrO1mgcZaVg&s=10", "Light, Medium Warm, Golden Tan, Deep Espresso", "8ml"),
        ("Lucky Beauty Lip Oil Gloss", 350, "Lips", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ387ikn6f3WR4gET1g-NqnEBhWKbW4r27OZrpjK_kHnQ&s=10", "Honey Tint, Rose Shimmer, Clear Dew, Berry Glaze", "5ml"),
        ("Lucky Beauty Eyeshadow Palette", 520, "Eyes", "Lucky Beauty", "https://ph-live-01.slatic.net/p/283e35f3b2d9146958b689c67bb977cf.jpg", "Lucky Nudes, Warm Sunset, Rose Glam", "8-Color"),
        ("Lucky Beauty Brow Pencil", 280, "Brows", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1nzhXpvoRCbS8L9SvQRYPpGLH6618IUbwRJ8SPPro5A&s", "Natural Brown, Dark Ash, Soft Black", "0.3g"),
        ("Lucky Beauty Makeup Primer", 450, "Face", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgHeFar_CRRw8p9Ab-dQMI2BU0is9IjM2BZJ80kE781g&s", "Standard", "25ml"),
        ("Lucky Beauty Velvet Lip Tint", 340, "Lips", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ3BYfEgMJOKbsiu7WcVzZi-HN0GbG64sSBT91eHQDVGQ&s", "Rosy Pink, Brick Red, Peach Nude, Berry Velvet", "4ml"),
        ("Lucky Beauty Blending Sponge", 160, "Tools", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRoepmA5v4B8WtBh5yPSxIim-9-Bn3hTEpsMLorebUEcA&s=10", "Standard", "1pc"),
        ("Lucky Beauty Lip Liner", 240, "Lips", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvnMLUvazRmV4RhbhBnw1pLbtcFE7UQmLdJHeChrrfWw&s", "Warm Nude, Mauve Magic, Classic Red, Deep Cocoa", "1.2g"),
        ("Lucky Beauty Complete Brush Set", 750, "Tools", "Lucky Beauty", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOhJRgFmNE8Cfh4VA1fCWFHhQbEF5AM26v_Ge2YVI8pQ&s=10", "Standard", "8pcs Set")
    ]
    
    for idx, (n, p, c, b, img, col, sz) in enumerate(raw_items):
        if idx < 40:
            original_price = round(float(p) / 0.8, 2)
        else:
            original_price = 0
            
        Product.objects.create(name=n, price=p, original_price=original_price, category=c, brand=b, image=img, colors=col, sizes=sz)

# --- TEMPLATES & SHARED COMPONENTS ---
FONT_LINK = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
FONT_FAMILY = "'Plus Jakarta Sans', sans-serif"

TOP_BAR_HTML = """<div class="walmart-top-bar"><a href="/" class="brand-logo"><i class="bi bi-bag-heart-fill"></i> <span class="d-none d-sm-inline">BELLE'S COUTURE</span><span class="d-inline d-sm-none">BELLE</span></a><form class="search-container" action="/" method="GET"><input type="hidden" name="cat" value="{{cat}}"><input type="hidden" name="brand" value="{{brand}}"><input type="text" name="q" class="search-input" placeholder="Search products..." value="{{q}}"><button type="submit" class="search-btn"><i class="bi bi-search"></i></button></form><div class="header-actions"><a href="/orders/" class="header-action-item"><i class="bi bi-box-seam"></i> <span class="d-none d-md-inline">Orders</span></a><a href="/appointments/" class="header-action-item"><i class="bi bi-calendar-event"></i> <span class="d-none d-md-inline">Book</span></a>{% if user.is_staff %}<a href="/artist-admin/" class="header-action-item" style="color:#d4af37;"><i class="bi bi-shield-check"></i> <span class="d-none d-lg-inline">Admin</span></a>{% endif %}<a href="/profile/" class="header-action-item"><i class="bi bi-person-circle"></i> <span class="d-none d-md-inline">Account</span></a><a href="/cart/" class="header-action-item position-relative"><i class="bi bi-cart3 fs-5"></i> <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill" style="background:#8C6D53; font-size:9px;">{{cart_count}}</span></a><a href="/logout/" class="header-action-item"><i class="bi bi-box-arrow-right"></i></a></div></div>"""

# --- PERSISTENT SUPPORT FOOTER ---
SUPPORT_FOOTER_HTML = """<footer class="text-center py-4 mt-5 border-top" style="background:#FFFFFF; border-color:#EFE8DE !important; font-size:12px; color:#6E5039;"><div class="container px-3"><div class="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2"><div><b>Belle's Couture</b> &copy; 2026 — Professional Beauty & Artistry</div><div><i class="bi bi-headset me-1"></i> Need help with products or your account? Email: <a href="mailto:makeupartistry@bellescouture.shop" class="fw-bold text-decoration-none" style="color:#8C6D53;">makeupartistry@bellescouture.shop</a></div></div></div></footer>"""

SHARED_STYLE = "body{background:#FAF7F2; color:#3D312A; font-family:" + FONT_FAMILY + "; margin:0; min-height:100vh; display:flex; flex-direction:column;} .walmart-top-bar{background:#FFFFFF; padding:10px 16px; display:flex; align-items:center; gap:12px; position:sticky; top:0; z-index:1000; border-bottom:1px solid #EFE8DE;} @media(min-width:768px){.walmart-top-bar{padding:12px 28px; gap:18px;}} .brand-logo{font-weight:800; font-size:1.2rem; color:#6E5039; text-decoration:none; white-space:nowrap;} @media(min-width:768px){.brand-logo{font-size:1.4rem;}} .search-container{flex:1; max-width:680px; position:relative;} .search-input{width:100%; border-radius:24px; border:1px solid #DFD5C6; background:#FAF7F2; padding:8px 38px 8px 14px; font-size:13px; outline:none;} @media(min-width:768px){.search-input{padding:9px 45px 9px 18px; font-size:14px;}} .search-btn{position:absolute; right:4px; top:50%; transform:translateY(-50%); background:#8C6D53; border:none; width:30px; height:30px; border-radius:50%; color:#fff; display:flex; align-items:center; justify-content:center; font-size:12px;} @media(min-width:768px){.search-btn{width:34px; height:34px; font-size:14px;}} .header-actions{display:flex; align-items:center; gap:12px; font-size:12px; font-weight:600; margin-left:auto;} @media(min-width:768px){.header-actions{gap:20px; font-size:13px;}} .header-action-item{color:#523B29; text-decoration:none; display:flex; align-items:center; gap:5px; white-space:nowrap;} .card-white{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:18px; margin-bottom:16px;} @media(min-width:768px){.card-white{padding:24px;}} .orig-price{text-decoration:line-through; color:#A39588; font-size:12px; margin-left:6px;}"

AUTH_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>body{background:#FAF7F2; min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:""" + FONT_FAMILY + """; color:#3D312A; padding:20px;} .box{background:#FFFFFF; border-radius:20px; padding:30px; width:100%; max-width:440px; box-shadow:0 10px 30px rgba(140,109,83,0.08); border:1px solid #EFE8DE;} @media(min-width:768px){.box{padding:40px;}} h4{color:#6E5039; font-weight:800; text-align:center} .btn-y{background:#8C6D53; color:#fff; border-radius:24px; width:100%; padding:12px; border:none; font-weight:700} .alert-success{background:#F0FDF4; border:1px solid #DCFCE7; color:#166534; font-size:13px; border-radius:12px; padding:12px 14px; font-weight:700;}</style><script>
function togglePassword(fieldId, iconId) {
    let input = document.getElementById(fieldId);
    let icon = document.getElementById(iconId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("bi-eye");
        icon.classList.add("bi-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("bi-eye-slash");
        icon.classList.add("bi-eye");
    }
}
</script></head><body><div class="box"><h4>BELLE'S COUTURE</h4><p class="text-center fw-bold mb-3" style="font-size:14px; color:#8C7B70;">{{title}}</p>{% if success_msg %}<div class="alert alert-success text-center"><i class="bi bi-check-circle-fill me-1"></i> {{success_msg|safe}}</div>{% endif %}{% if msg %}<div class="alert alert-danger text-center small">{{msg}}</div>{% endif %}<form method="POST" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}">{% for f in form %}<div class="mb-3"><label class="form-label small fw-bold" style="color:#6E5039;">{{f.label}}</label>{% if 'password' in f.name or 'confirm' in f.name %}<div class="input-group">{{f}}<span class="input-group-text" style="background:#FAF7F2; border:1px solid #DFD5C6; border-top-right-radius:10px; border-bottom-right-radius:10px; cursor:pointer;" onclick="togglePassword('{{f.id_for_label}}', 'eye_{{f.name}}')"><i class="bi bi-eye" id="eye_{{f.name}}" style="color:#8C6D53;"></i></span></div>{% else %}{{f}}{% endif %}{% if f.errors %}{% for err in f.errors %}<div style="color:#DC3545; font-size:12px; font-weight:600; margin-top:4px;">{{err}}</div>{% endfor %}{% endif %}</div>{% endfor %}<button class="btn-y mt-2">{{button}}</button></form><p class="text-center mt-3 small" style="color:#8C7B70;">{{footer|safe}}</p></div><div class="mt-4 text-center small text-muted px-3">Need help with your account? <a href="mailto:makeupartistry@bellescouture.shop" style="color:#8C6D53; font-weight:600;">makeupartistry@bellescouture.shop</a></div></body></html>"""

HOME_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Belle's Couture</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.sub-nav{background:#FFFFFF; border-bottom:1px solid #EFE8DE; padding:10px 16px; display:flex; align-items:center; gap:10px; overflow-x:auto; font-size:13px; font-weight:600;} @media(min-width:768px){.sub-nav{padding:10px 28px;}} .sub-nav::-webkit-scrollbar{height:4px;} .sub-nav::-webkit-scrollbar-thumb{background:#DFD5C6; border-radius:4px;} .sub-nav-item{color:#6E5039; text-decoration:none; padding:6px 14px; border-radius:20px; background:#F5EFE6; border:1px solid #E6DCCE; white-space:nowrap;} .sub-nav-item.active{background:#8C6D53; color:#fff;} 

.hero-grid{display:grid; grid-template-columns:1fr; gap:16px; margin:16px;} @media(min-width:768px){.hero-grid{grid-template-columns:1.6fr 1fr; gap:20px; margin:24px 28px;}} 
.main-banner{background:linear-gradient(135deg,#FAF5EE 0%,#F0E5D8 100%); border:1px solid #E4D7C3; border-radius:20px; padding:24px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 10px 30px rgba(140,109,83,0.05);} @media(min-width:768px){.main-banner{border-radius:24px; padding:36px;}} 

.discount-img-card{display:block; width:100%; height:100%; min-height:180px; border-radius:20px; overflow:hidden; position:relative; border:1px solid #D4AF37; box-shadow:0 10px 25px rgba(140,109,83,0.12); text-decoration:none; transition:transform 0.3s ease, box-shadow 0.3s ease;} @media(min-width:768px){.discount-img-card{border-radius:24px; min-height:220px;}}
.discount-img-card:hover{transform:translateY(-3px); box-shadow:0 14px 30px rgba(212,175,55,0.22);}
.discount-img-card img{width:100%; height:100%; object-fit:cover; filter:brightness(0.9); transition:transform 0.5s ease;}
.discount-img-card:hover img{transform:scale(1.04);}
.discount-img-overlay{position:absolute; inset:0; background:linear-gradient(to top, rgba(38,25,18,0.9) 0%, rgba(38,25,18,0.35) 60%, transparent 100%); display:flex; flex-direction:column; justify-content:flex-end; padding:16px; text-align:left; color:#fff;} @media(min-width:768px){.discount-img-overlay{padding:20px;}}

.product-card{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:12px; height:100%; display:flex; flex-direction:column; justify-content:space-between; transition:transform 0.2s;} @media(min-width:768px){.product-card{padding:14px;}}
.product-card:hover{transform:translateY(-3px); box-shadow:0 6px 20px rgba(140,109,83,0.1);} 
.product-card img{width:100%; height:140px; object-fit:cover; border-radius:12px; margin-bottom:10px;} @media(min-width:768px){.product-card img{height:160px; margin-bottom:12px;}}
.brand-tag{font-size:10px; font-weight:700; color:#8C6D53; text-transform:uppercase;} @media(min-width:768px){.brand-tag{font-size:11px;}}
.product-title{font-weight:600; font-size:13px; height:36px; overflow:hidden;} @media(min-width:768px){.product-title{font-size:14px; height:38px;}}
.price-tag{color:#6E5039; font-weight:800; font-size:16px;} @media(min-width:768px){.price-tag{font-size:18px;}}
.btn-view{background:#8C6D53; color:#fff; border-radius:20px; font-weight:700; border:none; width:100%; padding:7px; font-size:11px; text-align:center; display:block; text-decoration:none;} @media(min-width:768px){.btn-view{padding:8px; font-size:12px;}}
.btn-quick{background:#FAF7F2; color:#6E5039; border:1px solid #8C6D53; border-radius:20px; font-weight:700; width:100%; padding:7px; font-size:11px; text-align:center; cursor:pointer;} @media(min-width:768px){.btn-quick{padding:8px; font-size:12px;}}
.btn-quick:hover{background:#F5EFE6;}</style></head><body>""" + TOP_BAR_HTML + """<div class="sub-nav"><select onchange="location = this.value;" class="form-select form-select-sm fw-bold" style="width:160px; background:#F5EFE6; border-color:#E6DCCE; color:#6E5039; border-radius:20px; padding:6px 10px; font-size:12px;"><option value="/?cat=All&brand={{brand}}">Category: All</option><option value="/?cat=Face&brand={{brand}}" {% if cat == 'Face' %}selected{% endif %}>Face & Base</option><option value="/?cat=Eyes&brand={{brand}}" {% if cat == 'Eyes' %}selected{% endif %}>Eyes</option><option value="/?cat=Lips&brand={{brand}}" {% if cat == 'Lips' %}selected{% endif %}>Lips</option><option value="/?cat=Brows&brand={{brand}}" {% if cat == 'Brows' %}selected{% endif %}>Brows</option><option value="/?cat=Setting&brand={{brand}}" {% if cat == 'Setting' %}selected{% endif %}>Setting & Sprays</option><option value="/?cat=Skincare&brand={{brand}}" {% if cat == 'Skincare' %}selected{% endif %}>Skincare & Removers</option><option value="/?cat=Tools&brand={{brand}}" {% if cat == 'Tools' %}selected{% endif %}>Tools & Accessories</option><option value="/?cat=Specialty&brand={{brand}}" {% if cat == 'Specialty' %}selected{% endif %}>Specialty & Glow</option></select><a href="/?cat={{cat}}&brand=All" class="sub-nav-item {% if brand == 'All' %}active{% endif %}">All Brands</a><a href="/?cat={{cat}}&brand=Careline" class="sub-nav-item {% if brand == 'Careline' %}active{% endif %}">Careline</a><a href="/?cat={{cat}}&brand=Dazzle Me" class="sub-nav-item {% if brand == 'Dazzle Me' %}active{% endif %}">Dazzle Me</a><a href="/?cat={{cat}}&brand=O TWO O" class="sub-nav-item {% if brand == 'O TWO O' %}active{% endif %}">O.TWO.O</a><a href="/?cat={{cat}}&brand=Vice Cosmetics" class="sub-nav-item {% if brand == 'Vice Cosmetics' %}active{% endif %}">Vice Cosmetics</a><a href="/?cat={{cat}}&brand=BLK" class="sub-nav-item {% if brand == 'BLK' %}active{% endif %}">BLK</a><a href="/?cat={{cat}}&brand=Ever Bilena" class="sub-nav-item {% if brand == 'Ever Bilena' %}active{% endif %}">Ever Bilena</a><a href="/?cat={{cat}}&brand=GRWM Cosmetics" class="sub-nav-item {% if brand == 'GRWM Cosmetics' %}active{% endif %}">GRWM</a><a href="/?cat={{cat}}&brand=Issy Cosmetics" class="sub-nav-item {% if brand == 'Issy Cosmetics' %}active{% endif %}">Issy</a><a href="/?cat={{cat}}&brand=Lucky Beauty" class="sub-nav-item {% if brand == 'Lucky Beauty' %}active{% endif %}">Lucky Beauty</a></div><div class="hero-grid"><div class="main-banner"><span class="badge mb-2 px-3 py-1 align-self-start shadow-sm" style="background:#D4AF37; color:#1a120e; font-weight:700; font-size:10px; letter-spacing:1px;"><i class="bi bi-gem me-1"></i> LUXURY BEAUTY ARTISTRY</span><h1 style="font-weight:800; color:#3D2C22; font-size:1.5rem; letter-spacing:-0.5px; line-height:1.2;">Belle's Complete Beauty Essentials</h1><p class="mb-3 text-muted small" style="line-height:1.6; max-width:92%;">Explore professional makeup products ranging from high-end primers, foundations, to exquisite brushes and setting sprays.</p><div><a href="/appointments/" class="btn rounded-pill px-4 fw-bold py-2 shadow-sm" style="background:#6E5039; color:#fff; font-size:13px;"><i class="bi bi-stars me-1"></i> Book Makeup Artist</a></div></div><div class="p-0 m-0"><a href="/?discount=true" class="discount-img-card"><img src="https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&auto=format&fit=crop" alt="Discount Promo"><div class="discount-img-overlay"><span class="badge mb-1 px-2.5 py-1 align-self-start shadow-sm" style="background:#D4AF37; color:#1a120e; font-weight:800; font-size:10px; letter-spacing:1px;"><i class="bi bi-tag-fill me-1"></i> EXCLUSIVE VOUCHER</span><h5 class="fw-bold m-0" style="color:#fff; font-size:1.05rem; letter-spacing:0.3px;">20% OFF LUXURY COLLECTION</h5><p class="text-light m-0 mt-1" style="font-size:11px; opacity:0.85;">Tap here to reveal all discounted items & checkout!</p></div></a></div></div><div class="container-fluid px-3 px-md-4 mt-3 flex-grow-1"><div class="row g-2 g-md-3">{% for p in products %}<div class="col-6 col-md-4 col-lg-3"><div class="product-card"><div><img src="{{p.image}}"><div class="brand-tag">{{p.brand}}</div><div class="product-title">{{p.name}}</div></div><div><div><span class="price-tag">₱{{p.price}}</span>{% if p.original_price and p.original_price > p.price %}<span class="orig-price">₱{{p.original_price}}</span>{% endif %}</div><div class="d-grid gap-2 mt-2"><button type="button" class="btn-quick" data-bs-toggle="modal" data-bs-target="#quickModal{{p.id}}"><i class="bi bi-bag-plus"></i> Quick Shop</button><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><button type="submit" class="btn w-100 rounded-pill fw-bold py-1" style="background:#8C6D53; color:#fff; font-size:11px;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form><a href="/product/{{p.id}}/" class="btn-view">View Details</a></div></div></div></div><!-- Quick Shop Modal --><div class="modal fade" id="quickModal{{p.id}}" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4 border-0" style="background:#FAF7F2;"><div class="modal-header border-0 pb-0"><h5 class="modal-title fw-bold" style="color:#6E5039;">Quick Shop</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><div class="d-flex gap-3 align-items-center mb-3"><img src="{{p.image}}" style="width:80px; height:80px; object-fit:cover; border-radius:12px;"><div><b style="color:#523B29; font-size:14px;">{{p.name}}</b><div class="fs-5 fw-bold mt-1" style="color:#6E5039;">₱{{p.price}}{% if p.original_price and p.original_price > p.price %}<span class="orig-price fs-6 ms-2">₱{{p.original_price}}</span>{% endif %}</div></div></div><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Shade / Variant</label><select name="color" class="form-select form-select-sm" style="background:#FAF7F2; border-color:#DFD5C6; border-radius:10px;"><option value="Standard">Standard</option><option value="Shade 1">Shade 1</option><option value="Shade 2">Shade 2</option></select></div><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Quantity</label><input type="number" name="quantity" value="1" min="1" max="10" class="form-control form-control-sm" style="background:#FAF7F2; border-color:#DFD5C6; border-radius:10px;"></div><button type="submit" class="btn w-100 rounded-pill fw-bold py-2 mt-2" style="background:#8C6D53; color:#fff;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form></div></div></div></div>{% endfor %}</div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

PRODUCT_DETAIL_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{product.name}}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """:root { --primary-brown: #8C6D53; --dark-brown: #523B29; --light-bg: #FAF7F2; --border-color: #DFD5C6; }
.product-img-container{position:relative; overflow:hidden; border-radius:20px; background:#fff; border:1px solid #EFE8DE; box-shadow:0 8px 24px rgba(140,109,83,0.06); cursor:zoom-in; transition:transform 0.3s ease, box-shadow 0.3s ease;}
.product-img-container:hover{transform:translateY(-2px); box-shadow:0 12px 32px rgba(140,109,83,0.12);}
.product-img-container img{width:100%; max-height:380px; object-fit:cover; transition:transform 0.5s ease;} @media(min-width:768px){.product-img-container img{max-height:460px;}}
.product-img-container:hover img{transform:scale(1.03);}
.zoom-hint{position:absolute; bottom:16px; right:16px; background:rgba(82,59,41,0.85); color:#fff; padding:6px 12px; border-radius:20px; font-size:11px; font-weight:600; display:flex; align-items:center; gap:5px; backdrop-filter:blur(4px); opacity:0.9; transition:opacity 0.2s;}
.product-img-container:hover .zoom-hint{opacity:1;}
.detail-card{background:#fff; border-radius:20px; border:1px solid #EFE8DE; padding:20px; box-shadow:0 8px 24px rgba(140,109,83,0.05);} @media(min-width:768px){.detail-card{padding:32px;}}
.form-select, .form-control{background:var(--light-bg); border:1px solid var(--border-color); border-radius:14px; padding:10px 14px; font-size:13px; color:var(--dark-brown); font-family:""" + FONT_FAMILY + """; transition:all 0.2s;} @media(min-width:768px){.form-select, .form-control{padding:12px 16px; font-size:14px;}}
.form-select:focus, .form-control:focus{background:#fff; border-color:var(--primary-brown); box-shadow:0 0 0 4px rgba(140,109,83,0.1); outline:none;}
.btn-primary-y{background:var(--primary-brown); color:#fff; border-radius:24px; border:none; padding:12px 20px; font-weight:700; width:100%; font-size:14px; letter-spacing:0.3px; box-shadow:0 6px 18px rgba(140,109,83,0.2); transition:all 0.2s;} @media(min-width:768px){.btn-primary-y{padding:14px 24px; font-size:15px;}}
.btn-primary-y:hover{background:#755943; transform:translateY(-1px); box-shadow:0 8px 22px rgba(140,109,83,0.3); color:#fff;}
.badge-custom{background:linear-gradient(135deg, #8C6D53, #6E5039); color:#fff; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700; letter-spacing:0.5px; display:inline-block;}
</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 my-md-5 flex-grow-1" style="max-width:1100px;"><div class="row g-4 g-md-5 align-items-center"><div class="col-md-6"><div class="product-img-container" data-bs-toggle="modal" data-bs-target="#imageZoomModal"><img src="{{product.image}}" alt="{{product.name}}"><div class="zoom-hint"><i class="bi bi-search"></i> Click to Zoom</div></div></div><div class="col-md-6"><div class="detail-card"><div class="mb-3"><span class="badge-custom">{{product.brand}} | {{product.category}}</span></div><h2 class="fw-bold mb-3" style="color:var(--dark-brown); font-size:1.5rem; letter-spacing:-0.5px;">{{product.name}}</h2><div class="mb-3 mb-md-4 d-flex align-items-baseline gap-3"><span class="fs-2 fw-bold" style="color:var(--primary-brown);">₱{{product.price}}</span>{% if product.original_price and product.original_price > product.price %}<span class="orig-price fs-5">₱{{product.original_price}}</span>{% endif %}</div><p class="text-muted small mb-4" style="line-height:1.7;">{{product.description}}</p><form method="POST" action="/add-to-cart/{{product.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="fw-bold small mb-2 d-block" style="color:var(--dark-brown);"><i class="bi bi-palette me-1 text-muted"></i> Choose Shade / Variant</label><select name="color" class="form-select">{% for col in color_list %}<option value="{{col}}">{{col}}</option>{% endfor %}</select></div><div class="mb-3"><label class="fw-bold small mb-2 d-block" style="color:var(--dark-brown);"><i class="bi bi-rulers me-1 text-muted"></i> Choose Size / Edition</label><select name="size" class="form-select">{% for sz in size_list %}<option value="{{sz}}">{{sz}}</option>{% endfor %}</select></div><div class="mb-4"><label class="fw-bold small mb-2 d-block" style="color:var(--dark-brown);"><i class="bi bi-plus-slash-minus me-1 text-muted"></i> Quantity</label><input type="number" name="quantity" value="1" min="1" max="10" class="form-control"></div><button type="submit" class="btn-primary-y mt-2"><i class="bi bi-bag-plus me-2"></i> Add to Cart</button></form></div></div></div></div><!-- Fullscreen Zoom Modal --><div class="modal fade" id="imageZoomModal" tabindex="-1" aria-hidden="true"><div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content border-0 bg-transparent text-center"><div class="modal-body position-relative p-0"><button type="button" class="btn-close btn-close-white position-absolute top-0 end-0 m-3 z-3 bg-white p-2 rounded-circle shadow" data-bs-dismiss="modal" aria-label="Close"></button><img src="{{product.image}}" class="img-fluid rounded-4 shadow-lg" style="max-height:85vh; object-fit:contain; background:#1a120e; padding:10px;" alt="{{product.name}}"></div></div></div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

PROFILE_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Account Dashboard</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-y{background:#8C6D53; color:#fff; border-radius:24px; width:100%; padding:12px; border:none; font-weight:700;} .info-display-box{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:12px; padding:12px 16px; margin-bottom:16px;} .profile-input:read-only { background-color: #F8F5EE !important; border-color: #EFE8DE !important; color: #6E5039; }</style><script>
function toggleEditMode() {
    let inputs = document.querySelectorAll('.profile-input');
    let editBtn = document.getElementById('edit-btn-text');
    let saveBtnContainer = document.getElementById('save-btn-container');
    let passwordToggleCard = document.getElementById('password_toggle_card');
    let isReadonly = inputs[0].hasAttribute('readonly');
    
    inputs.forEach(input => {
        if(isReadonly) {
            input.removeAttribute('readonly');
            input.style.backgroundColor = '#FAF7F2';
        } else {
            input.setAttribute('readonly', 'readonly');
            input.style.backgroundColor = '#F8F5EE';
        }
    });
    
    if(isReadonly) {
        editBtn.innerHTML = '<i class="bi bi-x-circle me-1"></i> Cancel Editing';
        saveBtnContainer.style.display = 'block';
        passwordToggleCard.style.display = 'block';
    } else {
        editBtn.innerHTML = '<i class="bi bi-pencil-square me-1"></i> Edit Profile';
        saveBtnContainer.style.display = 'none';
        passwordToggleCard.style.display = 'none';
        let chk = document.getElementById('enable_password_change');
        if(chk) { chk.checked = false; togglePasswordSection(); }
    }
}
function togglePasswordSection() {
    let pwBox = document.getElementById('password_change_section');
    let chk = document.getElementById('enable_password_change');
    pwBox.style.display = chk.checked ? 'block' : 'none';
}
function togglePassword(fieldId, iconId) {
    let input = document.getElementById(fieldId);
    let icon = document.getElementById(iconId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("bi-eye");
        icon.classList.add("bi-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("bi-eye-slash");
        icon.classList.add("bi-eye");
    }
}
</script></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 my-md-5 flex-grow-1" style="max-width:960px;"><div class="row g-4"><div class="col-lg-4"><div class="card-white text-center"><div class="mb-3"><div class="rounded-circle d-inline-flex align-items-center justify-content-center fw-bold fs-3" style="width:72px; height:72px; background:#F5EFE6; color:#6E5039; border:2px solid #DFD5C6;"><i class="bi bi-person-fill"></i></div></div><h5 class="fw-bold mb-1" style="color:#523B29;">{{user.first_name}}</h5><p class="text-muted small mb-3">{{user.email}}</p><div class="d-grid gap-2 text-start mt-4"><a href="/orders/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#6E5039; border-color:#DFD5C6;"><i class="bi bi-box-seam me-2"></i> View My Orders</a><a href="/appointments/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#6E5039; border-color:#DFD5C6;"><i class="bi bi-calendar-event me-2"></i> My Artist Bookings</a>{% if user.is_staff %}<a href="/artist-admin/" class="btn btn-sm btn-outline-secondary rounded-pill py-2 px-3 fw-bold text-start" style="color:#d4af37; border-color:#DFD5C6;"><i class="bi bi-shield-check me-2"></i> Artist Admin Dashboard</a>{% endif %}<a href="/logout/" class="btn btn-sm btn-outline-danger rounded-pill py-2 px-3 fw-bold text-start"><i class="bi bi-box-arrow-right me-2"></i> Log Out</a></div></div></div><div class="col-lg-8"><div class="card-white"><div class="d-flex justify-content-between align-items-center mb-2"><div><h4 class="fw-bold m-0 fs-5 fs-md-4" style="color:#6E5039;"><i class="bi bi-pencil-square me-2"></i> Account Settings</h4></div><button type="button" class="btn btn-sm rounded-pill fw-bold px-3 py-1" onclick="toggleEditMode()" style="background:#F5EFE6; color:#6E5039; border:1px solid #DFD5C6; font-size:12px;"><span id="edit-btn-text"><i class="bi bi-pencil-square me-1"></i> Edit</span></button></div><p class="text-muted small mb-3">Click edit above to update your personal details or password.</p><hr>{% if success_msg %}<div class="alert alert-success rounded-3 mb-4"><i class="bi bi-check-circle-fill me-1"></i> {{success_msg}}</div>{% endif %}{% if msg %}<div class="alert alert-danger rounded-3 mb-4"><i class="bi bi-exclamation-triangle-fill me-1"></i> {{msg}}</div>{% endif %}<form method="POST"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="row g-3"><div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">Full name</label>{{form.full_name}}</div><div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">Email</label>{{form.email}}</div><div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">Phone</label>{{form.phone}}</div><div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">Address</label>{{form.address}}</div><div class="col-12"><label class="fw-bold small mb-1" style="color:#6E5039;">City</label>{{form.city}}</div></div><div id="password_toggle_card" class="mt-4 p-3 rounded-3" style="display:none; background:#FAF7F2; border:1px solid #DFD5C6;"><div class="form-check"><input class="form-check-input" type="checkbox" id="enable_password_change" onchange="togglePasswordSection()"><label class="form-check-label fw-bold small" for="enable_password_change" style="color:#6E5039;"><i class="bi bi-shield-lock me-1"></i> Change Password</label></div><div id="password_change_section" style="display:none;" class="mt-3 pt-3 border-top"><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Current Password</label><div class="input-group">{{form.current_password}}<span class="input-group-text" style="background:#FAF7F2; border:1px solid #DFD5C6; border-top-right-radius:10px; border-bottom-right-radius:10px; cursor:pointer;" onclick="togglePassword('{{form.current_password.id_for_label}}', 'eye_current_password')"><i class="bi bi-eye" id="eye_current_password" style="color:#8C6D53;"></i></span></div></div><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">New Password</label><div class="input-group">{{form.new_password}}<span class="input-group-text" style="background:#FAF7F2; border:1px solid #DFD5C6; border-top-right-radius:10px; border-bottom-right-radius:10px; cursor:pointer;" onclick="togglePassword('{{form.new_password.id_for_label}}', 'eye_new_password')"><i class="bi bi-eye" id="eye_new_password" style="color:#8C6D53;"></i></span></div></div></div></div><div id="save-btn-container" style="display:none;" class="mt-4"><button class="btn-y">Save Changes</button></div></form></div></div></div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

CART_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cart</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-blue{background:#8C6D53; color:#fff; border-radius:24px; border:none; padding:12px; font-weight:700; width:100%} .product-card{background:#fff; border-radius:16px; border:1px solid #EFE8DE; padding:12px; height:100%; display:flex; flex-direction:column; justify-content:space-between;} .product-card img{width:100%; height:120px; object-fit:cover; border-radius:12px; margin-bottom:8px;} .brand-tag{font-size:10px; font-weight:700; color:#8C6D53; text-transform:uppercase;} .product-title{font-weight:600; font-size:12px; height:32px; overflow:hidden;} .price-tag{color:#6E5039; font-weight:800; font-size:15px;}</style><script>function toggleAddressMode(){let mode = document.querySelector('input[name="address_mode"]:checked').value;let customDiv = document.getElementById('custom_address_section');if(mode === 'custom'){customDiv.style.display = 'block';document.getElementById('c_addr').required = true;}else{customDiv.style.display = 'none';document.getElementById('c_addr').required = false;}}</script></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 flex-grow-1"><div class="row g-4"><div class="col-lg-7"><div class="card-white"><h5 class="fw-bold fs-5" style="color:#6E5039;">Shopping Cart ({{count}} items)</h5><hr>{% if items %}{% for it in items %}<div class="d-flex gap-3 py-3 border-bottom"><img style="width:70px; height:70px; object-fit:cover; border-radius:10px;" src="{{it.product.image}}"><div class="flex-grow-1"><div class="fw-bold fs-6">{{it.product.name}}</div><small class="text-muted">{{it.product.brand}}</small><div class="small mt-1" style="color:#8C7B70;">{% if it.color %}Shade: <b>{{it.color}}</b>{% endif %}{% if it.size %} | Size: <b>{{it.size}}</b>{% endif %}</div><div class="mt-2"><span class="badge bg-light text-dark border">Qty: {{it.qty}}</span><a href="/remove/{{it.index}}/" class="btn btn-sm btn-outline-danger rounded-pill ms-2" style="font-size:10px">Remove</a></div></div><div class="text-end"><span class="price-tag">₱{{it.product.price}}</span>{% if it.product.original_price and it.product.original_price > it.product.price %}<br><span class="orig-price">₱{{it.product.original_price}}</span>{% endif %}<div class="fw-bold mt-2" style="color:#6E5039; font-size:14px;">₱{{it.subtotal}}</div></div></div>{% endfor %}<div class="text-end mt-3"><h5 class="fw-bold fs-5">Subtotal: <span style="color:#6E5039;">₱{{total}}</span></h5></div>{% else %}<div class="text-center py-5"><h6>Your cart is empty</h6><a href="/" class="btn rounded-pill mt-2" style="background:#8C6D53; color:#fff;">Shop Now</a></div>{% endif %}</div></div><div class="col-lg-5"><div class="card-white"><h6 class="fw-bold mb-3" style="color:#6E5039;">Cash On Delivery Checkout</h6>{% if items %}<form method="POST" action="/checkout/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="small fw-bold">Full Name</label><input class="form-control form-control-sm" name="full_name" value="{{user.first_name}}" required></div><div class="mb-3"><label class="small fw-bold mb-2">Delivery Address & Contact</label><div class="form-check"><input class="form-check-input" type="radio" name="address_mode" id="use_profile" value="profile" checked onchange="toggleAddressMode()"><label class="form-check-label small" for="use_profile">Use Account Info <br><span class="text-muted" style="font-size:11px;">(Phone: <b>{% if profile.phone %}{{profile.phone}}{% else %}Not set{% endif %}</b>, Address: <b>{% if profile.address %}{{profile.address}}, {{profile.city}}{% else %}Not set{% endif %}</b>)</span></label></div><div class="form-check mt-2"><input class="form-check-input" type="radio" name="address_mode" id="use_custom" value="custom" onchange="toggleAddressMode()"><label class="form-check-label small" for="use_custom">Use Another Address</label></div></div><div id="custom_address_section" style="display:none;" class="mb-3 p-3 rounded-3" style="background:#FAF7F2; border:1px solid #DFD5C6;"><div class="mb-2"><label class="small fw-bold">Alternate Phone</label><input class="form-control form-control-sm" name="alt_phone" placeholder="Phone Number"></div><div><label class="small fw-bold">Alternate Address & City</label><textarea class="form-control form-control-sm" name="alt_address" id="c_addr" rows="2" placeholder="Street, Barangay, City"></textarea></div></div><hr><div class="d-flex justify-content-between fw-bold mb-3"><span>Total</span><span style="color:#6E5039;">₱{{total}}</span></div><button class="btn-blue">Place Order - COD</button></form>{% endif %}</div></div></div><div class="row mt-4"><div class="col-12"><div class="card-white"><h5 class="fw-bold mb-3 fs-5" style="color:#6E5039;"><i class="bi bi-stars"></i> You May Also Like</h5><div class="row g-2">{% for p in products %}<div class="col-6 col-md-3"><div class="product-card"><div><img src="{{p.image}}"><div class="brand-tag">{{p.brand}}</div><div class="product-title">{{p.name}}</div></div><div class="mt-2"><div><span class="price-tag">₱{{p.price}}</span>{% if p.original_price and p.original_price > p.price %}<span class="orig-price">₱{{p.original_price}}</span>{% endif %}</div><div class="d-grid gap-2 mt-2"><form method="POST" action="/add-to-cart/{{p.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><button type="submit" class="btn w-100 rounded-pill fw-bold py-1" style="background:#8C6D53; color:#fff; font-size:11px;"><i class="bi bi-cart-plus"></i> Add to Cart</button></form><a href="/product/{{p.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill py-0" style="font-size:11px;">View</a></div></div></div></div>{% endfor %}</div></div></div></div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

ORDER_SUCCESS_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">""" + FONT_LINK + """<style>body{background:#FAF7F2; display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; font-family:""" + FONT_FAMILY + """; padding:20px;}.success-card{background:#fff; border-radius:24px; border:1px solid #EFE8DE; padding:30px; max-width:550px; width:100%; text-align:center;} @media(min-width:768px){.success-card{padding:40px;}}</style></head><body><div class="success-card flex-grow-1 d-flex flex-column justify-content-center m-auto"><h3 class="fw-bold fs-4" style="color:#6E5039;">Order Placed Successfully!</h3><div class="p-3 text-start rounded-3 mb-4" style="background:#FAF7F2; border:1px solid #EFE8DE;"><div class="d-flex justify-content-between"><b>Order ID:</b> <span>#{{order.id}}</span></div><div class="d-flex justify-content-between"><b>Total:</b> <span>₱{{order.total_amount}}</span></div></div><div class="d-flex flex-column flex-sm-row justify-content-center gap-2"><a href="/orders/" class="btn rounded-pill px-4" style="background:#8C6D53; color:#fff;">View Order</a> <a href="/" class="btn rounded-pill px-4 border">Continue Shopping</a></div></div>""" + SUPPORT_FOOTER_HTML + """</body></html>"""

ORDERS_DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Orders Dashboard</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.order-card{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:16px; padding:16px; margin-bottom:16px; transition:all 0.2s;} @media(min-width:768px){.order-card{padding:20px;}} .order-card:hover{box-shadow:0 6px 18px rgba(140,109,83,0.08);} .item-row{display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px dashed #E6DCCE;} .item-row:last-child{border-bottom:none;} .status-badge{font-size:10px; font-weight:700; padding:5px 10px; border-radius:20px; text-transform:uppercase;} @media(min-width:768px){.status-badge{font-size:11px; padding:6px 12px;}}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 my-md-4 flex-grow-1" style="max-width:880px;"><div class="card-white"><div class="mb-3"><h4 class="fw-bold m-0 fs-5 fs-md-4" style="color:#6E5039;"><i class="bi bi-box-seam"></i> My Orders Dashboard</h4></div><p class="text-muted small mb-4">Review your purchase history, check delivery details, or manage order statuses.</p><hr>{% if orders %}{% for o in orders %}<div class="order-card"><div class="d-flex flex-column flex-sm-row justify-content-between align-items-start align-items-sm-center gap-2 mb-3 pb-2 border-bottom"><div><h6 class="fw-bold mb-1" style="color:#6E5039;">Order #{{o.id}}</h6><small class="text-muted"><i class="bi bi-clock"></i> Placed on {{o.created_at|date:"M d, Y"}}</small></div><div>{% if o.status == 'Cancelled' %}<span class="status-badge bg-danger text-white"><i class="bi bi-x-circle"></i> Cancelled</span>{% elif o.status == 'In Transit' %}<span class="status-badge bg-info text-dark"><i class="bi bi-truck"></i> In Transit</span>{% elif o.status == 'Delivered' %}<span class="status-badge bg-success text-white"><i class="bi bi-check-all"></i> Delivered</span>{% else %}<span class="status-badge" style="background:#E2E8F0; color:#1E293B;"><i class="bi bi-hourglass-split"></i> {{o.status}}</span>{% endif %}</div></div><div class="my-3">{% for item in o.items.all %}<div class="item-row"><img src="{{item.product.image}}" style="width:48px; height:48px; object-fit:cover; border-radius:8px; border:1px solid #DFD5C6;"><div class="flex-grow-1"><div class="fw-bold" style="color:#523B29; font-size:13px;">{{item.product.name}}</div><div class="small text-muted" style="font-size:11px;">{% if item.selected_color %}Shade: <b>{{item.selected_color}}</b>{% endif %}{% if item.selected_size %} | Size: <b>{{item.selected_size}}</b>{% endif %} | Qty: <b>{{item.quantity}}</b></div></div><div class="fw-bold" style="color:#6E5039; font-size:14px;">₱{{item.price}}</div></div>{% endfor %}</div><div class="p-3 rounded-3 mb-3" style="background:#FFFFFF; border:1px solid #E6DCCE;"><div class="row small"><div class="col-md-7"><b>Delivery Address:</b><br><span class="text-muted">{{o.full_name}} — {{o.address}} (Ph: {{o.phone}})</span></div><div class="col-md-5 text-md-end mt-2 mt-md-0"><span class="text-muted">Total Amount:</span><br><span class="fs-5 fw-bold" style="color:#6E5039;">₱{{o.total_amount}}</span></div></div></div><div class="d-flex justify-content-end gap-2">{% if o.status != 'Cancelled' and o.status != 'Delivered' %}<button type="button" class="btn btn-sm rounded-pill px-3 fw-bold shadow-sm" data-bs-toggle="modal" data-bs-target="#cancelOrderModal{{o.id}}" style="background:#FAF7F2; color:#DC3545; border:1px solid #DC3545; font-size:12px;"><i class="bi bi-x-circle me-1"></i> Cancel Order</button>{% elif o.status == 'Cancelled' or o.status == 'Delivered' %}<a href="/delete-order/{{o.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill fw-bold"><i class="bi bi-trash me-1"></i> Remove from History</a>{% endif %}</div></div><!-- Elegant Cancel Confirmation Modal --><div class="modal fade" id="cancelOrderModal{{o.id}}" tabindex="-1" aria-hidden="true"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4 border-0 shadow-lg" style="background:#FAF7F2; border:1px solid #DFD5C6;"><div class="modal-header border-0 pb-0 pt-4 px-4"><h5 class="modal-title fw-bold fs-5" style="color:#523B29;"><i class="bi bi-exclamation-triangle text-danger me-2"></i> Cancel Order #{{o.id}}</h5><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div><div class="modal-body px-4 py-3"><p class="text-muted small mb-0" style="line-height:1.6;">Are you sure you want to cancel this order? This action cannot be undone, and your reservation will be released.</p></div><div class="modal-footer border-0 px-4 pb-4 pt-2"><button type="button" class="btn btn-sm rounded-pill px-4 fw-bold" data-bs-dismiss="modal" style="background:#EFE8DE; color:#6E5039; border:none;">Keep Order</button><a href="/cancel-order/{{o.id}}/" class="btn btn-sm rounded-pill px-4 fw-bold shadow-sm" style="background:#DC3545; color:#fff;">Yes, Cancel Order</a></div></div></div></div>{% endfor %}{% else %}<div class="text-center py-5"><div class="mb-3 fs-1 text-muted"><i class="bi bi-bag-x"></i></div><h6 class="fw-bold" style="color:#523B29;">No orders placed yet</h6><p class="text-muted small">Explore our professional beauty collection and place your first order!</p><a href="/" class="btn rounded-pill px-4 fw-bold mt-2" style="background:#8C6D53; color:#fff;">Start Shopping</a></div>{% endif %}</div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

APPOINTMENT_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bookings</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.btn-blue{background:#8C6D53; color:#fff; border-radius:24px; border:none; padding:12px; font-weight:700; width:100%} .package-card{display:block; padding:14px; border-radius:12px; background:#FAF7F2; border:1px solid #DFD5C6; cursor:pointer; height:100%;} .package-card input{display:none} .package-card:has(input:checked){background:#F5EFE6; border-color:#8C6D53; box-shadow:0 0 0 1px #8C6D53} .booking-card{background:#FAF7F2; border:1px solid #EFE8DE; border-radius:12px; padding:16px; margin-bottom:12px}
</style><script>
const bookedDates = {{ booked_dates_json|safe }};

function checkDateAvailability() {
    let dateInput = document.getElementById('booking_date');
    let timeInput = document.getElementById('booking_time');
    let submitBtn = document.getElementById('submit_booking_btn');
    let alertBox = document.getElementById('slot_warning_alert');
    let statusText = document.getElementById('slot_status_text');
    
    if(!dateInput || !timeInput) return;
    let selDate = dateInput.value;
    
    if(selDate) {
        let isBooked = bookedDates.includes(selDate);
        
        if(isBooked) {
            alertBox.style.display = 'block';
            dateInput.title = "Date Fully Booked / Unavailable";
            timeInput.disabled = true;
            timeInput.value = "";
            timeInput.style.opacity = '0.45';
            timeInput.style.backgroundColor = '#E9ECEF';
            statusText.innerHTML = '<i class="bi bi-x-circle-fill text-danger me-1"></i> <span class="text-danger fw-bold">Slot Booked! This date is already reserved by another customer. Time selection is locked.</span>';
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.5';
            submitBtn.innerText = 'Date Fully Booked / Unavailable';
        } else {
            alertBox.style.display = 'none';
            dateInput.title = "";
            timeInput.disabled = false;
            timeInput.style.opacity = '1';
            timeInput.style.backgroundColor = '#FAF7F2';
            statusText.innerHTML = '<i class="bi bi-check-circle-fill text-success me-1"></i> <span class="text-success fw-bold">This date and time slot is available!</span>';
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.innerText = 'Confirm Booking';
        }
    }
}
</script></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 flex-grow-1"><div class="row g-4"><div class="col-lg-8"><div class="card-white"><h4 class="fw-bold fs-5 fs-md-4" style="color:#6E5039;">Book Your Makeup Artist</h4>{% if error %}<div class="alert alert-danger rounded-3"><i class="bi bi-exclamation-triangle-fill me-1"></i> {{error}}</div>{% endif %}{% if success %}<div class="alert alert-success rounded-3"><i class="bi bi-check-circle-fill me-1"></i> {{success}}</div>{% endif %}<div id="slot_warning_alert" class="alert alert-danger rounded-3" style="display:none;"><i class="bi bi-exclamation-triangle-fill me-1"></i> <b>Slot Booked!</b> This date is already reserved by another customer. Time selection is disabled. Please choose a different date.</div><form method="POST" id="booking_form"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><h6 class="fw-bold mt-2 mb-3">1. Select Service Package</h6><div class="row g-2"><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Graduation Glam" checked><div class="fw-bold small">Graduation Glam</div><small class="text-muted" style="font-size:11px;">₱2,500 | Full Lash & Hair</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Normal Day Natural"><div class="fw-bold small">Normal Day Natural</div><small class="text-muted" style="font-size:11px;">₱1,500 | Fresh Everyday</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Event Glam"><div class="fw-bold small">Event Glam</div><small class="text-muted" style="font-size:11px;">₱3,000 | Party & Gala</small></label></div><div class="col-6"><label class="package-card"><input type="radio" name="service_type" value="Bridal Glow"><div class="fw-bold small">Bridal Glow</div><small class="text-muted" style="font-size:11px;">₱4,500 | Weddings</small></label></div></div><h6 class="fw-bold mt-4">2. Date & Time Selection</h6><div class="row g-2"><div class="col-6"><input type="date" id="booking_date" name="date" class="form-control form-control-sm" required min="{{today}}" onchange="checkDateAvailability()" title=""></div><div class="col-6"><input type="time" id="booking_time" name="time" class="form-control form-control-sm" required></div></div><div class="mt-2 small" id="slot_status_text"></div><h6 class="fw-bold mt-4">3. Customer Info</h6><div class="row g-2"><div class="col-12"><input name="customer_name" class="form-control form-control-sm" value="{{user.first_name}} {{user.last_name}}" placeholder="Full Name" required></div><div class="col-6"><input name="email" type="email" class="form-control form-control-sm" value="{{user.email}}" placeholder="Email" required></div><div class="col-6"><input name="phone" class="form-control form-control-sm" placeholder="Phone" value="{{profile.phone}}" required></div><div class="col-12"><input name="address" class="form-control form-control-sm" placeholder="Complete Address" value="{{profile.address}}" required></div><div class="col-6"><input name="city" class="form-control form-control-sm" placeholder="City" value="{{profile.city}}" required></div><div class="col-6"><input name="event_type" class="form-control form-control-sm" placeholder="Event Category" required></div><div class="col-12"><textarea name="additional_request" class="form-control form-control-sm" placeholder="Additional requests" rows="2"></textarea></div></div><button type="submit" id="submit_booking_btn" class="btn-blue mt-4">Confirm Booking</button></form></div></div><div class="col-lg-4"><div class="card-white"><h6 class="fw-bold mb-3" style="color:#6E5039;"><i class="bi bi-calendar-check"></i> Your Bookings</h6>{% if bookings %}{% for b in bookings %}<div class="booking-card"><div class="d-flex justify-content-between align-items-start"><div><b class="small" style="color:#6E5039;">{{b.service_type}}</b><div class="small text-muted mt-1" style="font-size:11px;"><i class="bi bi-calendar"></i> Date: {{b.date|date:"M. d, Y"}}<br><i class="bi bi-geo-alt"></i> City: {{b.city}}</div></div><span class="badge {% if b.status == 'Declined' or b.status == 'Cancelled' %}bg-danger{% elif b.status == 'Accepted' %}bg-success{% else %}bg-warning text-dark{% endif %}" style="font-size:9px;">{{b.status}}</span></div>{% if b.status == 'Declined' %}<div class="mt-2 p-2 rounded-3 small" style="background:#FEE2E2; border:1px solid #FECACA; color:#991B1B;"><div class="fw-bold mb-1"><i class="bi bi-exclamation-triangle-fill me-1"></i> Reservation Declined</div>{% if b.decline_reason %}<div><b>Reason:</b> {{b.decline_reason}}</div>{% endif %}<div class="mt-2 pt-2 border-top border-danger-subtle"><a href="/appointments/" class="btn btn-sm btn-danger rounded-pill fw-bold w-100" style="font-size:11px;"><i class="bi bi-arrow-repeat me-1"></i> Book Another Date</a></div></div>{% endif %}{% if b.status == 'Cancelled' and b.cancelled_at %}<div class="mt-2 p-2 rounded-2 small text-danger" style="background:#FEE2E2; border:1px solid #FECACA;"><i class="bi bi-x-circle-fill"></i> Cancelled on: {{b.cancelled_at|date:"M. d, Y"}}</div>{% endif %}<div class="d-grid gap-2 mt-3"><button class="btn btn-sm rounded-pill fw-bold" data-bs-toggle="modal" data-bs-target="#detailsModal{{b.id}}" style="background:#fff; border:1px solid #8C6D53; color:#6E5039; font-size:11px;"><i class="bi bi-eye"></i> Review Details</button>{% if b.status != 'Cancelled' and b.status != 'Declined' %}<a href="/cancel-booking/{{b.id}}/" class="btn btn-sm btn-outline-danger rounded-pill" style="font-size:11px;">Cancel</a>{% else %}<a href="/delete-booking/{{b.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill" style="font-size:11px;">Delete</a>{% endif %}</div></div><div class="modal fade" id="detailsModal{{b.id}}" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4"><div class="modal-header border-0" style="background:#FAF7F2;"><h6 class="modal-title fw-bold" style="color:#6E5039;"><i class="bi bi-receipt"></i> Booking Details #{{b.id}}</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body small"><div class="row g-2"><div class="col-12"><b>Service:</b> {{b.service_type}}</div><div class="col-6"><b>Event Type:</b> {{b.event_type}}</div><div class="col-6"><b>Status:</b> <span class="badge {% if b.status == 'Declined' or b.status == 'Cancelled' %}bg-danger{% elif b.status == 'Accepted' %}bg-success{% else %}bg-warning text-dark{% endif %}">{{b.status}}</span></div>{% if b.status == 'Declined' and b.decline_reason %}<div class="col-12 p-2 rounded-2" style="background:#FEE2E2; color:#991B1B;"><b>Decline Reason:</b> {{b.decline_reason}}</div>{% endif %}<div class="col-6"><b>Date:</b> {{b.date|date:"M. d, Y"}}</div><div class="col-6"><b>Time:</b> {{b.time}}</div><hr class="my-2"><div class="col-12"><b>Customer:</b> {{b.customer_name}}</div><div class="col-12"><b>Email:</b> {{b.email}}</div><div class="col-12"><b>Phone:</b> {{b.phone}}</div><div class="col-12"><b>Address:</b> {{b.address}}</div><div class="col-12"><b>City:</b> {{b.city}}</div><div class="col-12"><b>Additional Request:</b><br><em>{% if b.additional_request %}{{b.additional_request}}{% else %}None{% endif %}</em></div><hr class="my-2"><div class="col-12"><b>Booked On:</b> {{b.created_at|date:"M. d, Y"}}</div></div></div><div class="modal-footer border-0"><button type="button" class="btn btn-sm rounded-pill px-3" style="background:#8C6D53; color:#fff;" data-bs-dismiss="modal">Close</button></div></div></div></div>{% endfor %}{% else %}<p class="small text-muted text-center py-3">No bookings yet</p>{% endif %}</div></div></div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

ARTIST_ADMIN_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Artist Admin - Management Hub</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">""" + FONT_LINK + """<style>""" + SHARED_STYLE + """.admin-card{background:#FAF7F2; border:1px solid #DFD5C6; border-radius:16px; padding:16px; margin-bottom:16px;} @media(min-width:768px){.admin-card{padding:20px;}} .nav-tabs .nav-link{color:#6E5039; font-weight:700; border:none; border-bottom:3px solid transparent; border-radius:0; padding:10px 20px;} .nav-tabs .nav-link.active{background:transparent; color:#523B29; border-bottom-color:#8C6D53;} .item-row{display:flex; align-items:center; gap:12px; padding:8px 0; border-bottom:1px dashed #E6DCCE;} .item-row:last-child{border-bottom:none;}</style></head><body>""" + TOP_BAR_HTML + """<div class="container my-3 my-md-4 flex-grow-1" style="max-width:1000px;"><div class="card-white"><div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3 mb-4"><div><h4 class="fw-bold m-0 fs-5 fs-md-4" style="color:#6E5039;"><i class="bi bi-shield-check"></i> Makeup Artist Administration Hub</h4><p class="text-muted small m-0">Review product purchases, prepare orders, update shipping, and manage reservations.</p></div><div class="d-flex align-items-center gap-2"><a href="/profile/" class="btn btn-sm rounded-pill fw-bold" style="background:#F5EFE6; color:#6E5039; border:1px solid #DFD5C6;"><i class="bi bi-key"></i> Password</a></div></div><!-- Nav Tabs --><ul class="nav nav-tabs mb-4" id="adminTab" role="tablist"><li class="nav-item" role="presentation"><button class="nav-link active" id="orders-tab" data-bs-toggle="tab" data-bs-target="#orders-pane" type="button" role="tab"><i class="bi bi-box-seam me-1"></i> Product Orders ({{orders|length}})</button></li><li class="nav-item" role="presentation"><button class="nav-link" id="bookings-tab" data-bs-toggle="tab" data-bs-target="#bookings-pane" type="button" role="tab"><i class="bi bi-calendar-event me-1"></i> Makeup Bookings ({{bookings|length}})</button></li></ul><div class="tab-content" id="adminTabContent"><!-- Product Orders Pane --><div class="tab-pane fade show active" id="orders-pane" role="tabpanel">{% if orders %}{% for o in orders %}<div class="admin-card"><div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-2 mb-3 pb-2 border-bottom"><div><h5 class="fw-bold m-0 fs-6" style="color:#523B29;">Order #{{o.id}} — <span style="color:#8C6D53;">{{o.full_name}}</span></h5><small class="text-muted"><i class="bi bi-clock"></i> Placed on {{o.created_at|date:"M d, Y"}}</small></div><div>{% if o.status == 'Cancelled' %}<span class="badge bg-danger">Cancelled</span>{% elif o.status == 'In Transit' %}<span class="badge bg-info text-dark">In Transit</span>{% elif o.status == 'Delivered' %}<span class="badge bg-success">Delivered</span>{% else %}<span class="badge bg-warning text-dark">{{o.status}}</span>{% endif %}</div></div><div class="my-3">{% for item in o.items.all %}<div class="item-row"><img src="{{item.product.image}}" style="width:48px; height:48px; object-fit:cover; border-radius:8px; border:1px solid #DFD5C6;"><div class="flex-grow-1"><div class="fw-bold" style="color:#523B29; font-size:13px;">{{item.product.name}}</div><div class="small text-muted" style="font-size:11px;">{% if item.selected_color %}Shade: <b>{{item.selected_color}}</b>{% endif %}{% if item.selected_size %} | Size: <b>{{item.selected_size}}</b>{% endif %} | Qty: <b>{{item.quantity}}</b></div></div><div class="fw-bold" style="color:#6E5039; font-size:14px;">₱{{item.price}}</div></div>{% endfor %}</div><div class="p-3 rounded-3 mb-3" style="background:#FFFFFF; border:1px solid #E6DCCE;"><div class="row small"><div class="col-md-7"><b>Delivery & Contact Info:</b><br><span class="text-muted">{{o.address}} (Ph: {{o.phone}})</span></div><div class="col-md-5 text-md-end mt-2 mt-md-0"><span class="text-muted">Total Amount:</span><br><span class="fs-5 fw-bold" style="color:#6E5039;">₱{{o.total_amount}} ({{o.payment_method}})</span></div></div></div><div class="d-flex flex-wrap justify-content-end gap-2">{% if o.status != 'Cancelled' and o.status != 'Delivered' %}{% if o.status == 'Processing' %}<a href="/artist-admin/order-status/{{o.id}}/In Transit/" class="btn btn-sm rounded-pill fw-bold" style="background:#0dcaf0; color:#000; font-size:12px;"><i class="bi bi-truck me-1"></i> Mark In Transit</a>{% endif %}<a href="/artist-admin/order-status/{{o.id}}/Delivered/" class="btn btn-sm rounded-pill fw-bold" style="background:#198754; color:#fff; font-size:12px;"><i class="bi bi-check-all me-1"></i> Mark Delivered</a>{% endif %}{% if o.status == 'Delivered' or o.status == 'Cancelled' %}<a href="/artist-admin/delete-order/{{o.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill fw-bold" style="font-size:12px;"><i class="bi bi-trash me-1"></i> Remove Order</a>{% endif %}</div></div>{% endfor %}{% else %}<div class="text-center py-5"><div class="mb-3 fs-1 text-muted"><i class="bi bi-box"></i></div><h6 class="fw-bold" style="color:#523B29;">No product orders yet</h6><p class="text-muted small">Customer purchases will appear here for preparation and shipping.</p></div>{% endif %}</div><!-- Bookings Pane --><div class="tab-pane fade" id="bookings-pane" role="tabpanel">{% if bookings %}{% for b in bookings %}<div class="admin-card"><div class="row align-items-center"><div class="col-md-7"><div class="d-flex align-items-center gap-2 mb-1"><h5 class="fw-bold m-0 fs-6" style="color:#523B29;">{{b.customer_name}}</h5><span class="badge {% if b.status == 'Accepted' %}bg-success{% elif b.status == 'Declined' or b.status == 'Cancelled' %}bg-danger{% else %}bg-warning text-dark{% endif %}" style="font-size:10px;">{{b.status}}</span></div><div class="small fw-bold" style="color:#8C6D53;"><i class="bi bi-stars"></i> Package: {{b.service_type}} ({{b.event_type}})</div><div class="small text-muted mt-1" style="font-size:11px;"><i class="bi bi-calendar-event"></i> Date: <b>{{b.date|date:"M. d, Y"}}</b> at {{b.time}}<br><i class="bi bi-geo-alt"></i> Location: {{b.address}}, {{b.city}}<br><i class="bi bi-telephone"></i> Contact: {{b.phone}} | <i class="bi bi-envelope"></i> {{b.email}}</div>{% if b.additional_request %}<div class="small mt-2 p-2 rounded-2" style="background:#FFF; border:1px solid #EFE8DE; font-size:11px;"><b>Request:</b> <em>{{b.additional_request}}</em></div>{% endif %}{% if b.status == 'Declined' and b.decline_reason %}<div class="small text-danger mt-2 p-2 rounded-2" style="background:#FEE2E2; border:1px solid #FECACA; font-size:11px;"><b>Decline Reason Sent:</b> {{b.decline_reason}}</div>{% endif %}{% if b.status == 'Cancelled' and b.cancelled_at %}<div class="small text-danger mt-1" style="font-size:11px;"><i class="bi bi-x-circle-fill"></i> Cancelled on: {{b.cancelled_at|date:"M d, Y"}}</div>{% endif %}</div><div class="col-md-5 text-md-end mt-3 mt-md-0"><div class="d-flex flex-column gap-2">{% if b.status != 'Accepted' %}<a href="/artist-admin/status/{{b.id}}/Accepted/" class="btn btn-sm rounded-pill fw-bold" style="background:#198754; color:#fff; font-size:12px;"><i class="bi bi-check-circle"></i> Accept Reservation</a>{% endif %}{% if b.status != 'Completed' and b.status != 'Declined' and b.status != 'Cancelled' %}<a href="/artist-admin/status/{{b.id}}/Completed/" class="btn btn-sm rounded-pill fw-bold" style="background:#6E5039; color:#fff; font-size:12px;"><i class="bi bi-flag-fill"></i> Mark Completed</a>{% endif %}{% if b.status != 'Declined' and b.status != 'Completed' and b.status != 'Cancelled' %}<button type="button" class="btn btn-sm btn-outline-danger rounded-pill fw-bold" data-bs-toggle="modal" data-bs-target="#declineModal{{b.id}}" style="font-size:12px;"><i class="bi bi-x-circle"></i> Decline / Slot Booked</button>{% endif %}{% if b.status == 'Cancelled' or b.status == 'Declined' or b.status == 'Completed' %}<a href="/artist-admin/delete-booking/{{b.id}}/" class="btn btn-sm btn-outline-secondary rounded-pill fw-bold" style="font-size:12px;"><i class="bi bi-trash me-1"></i> Remove Booking</a>{% endif %}</div></div></div></div><!-- Decline Reason Modal --><div class="modal fade" id="declineModal{{b.id}}" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4 border-0" style="background:#FAF7F2;"><div class="modal-header border-0 pb-0"><h5 class="modal-title fw-bold text-danger fs-6"><i class="bi bi-exclamation-triangle-fill"></i> Decline Reservation #{{b.id}}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body text-start"><form method="POST" action="/artist-admin/decline/{{b.id}}/"><input type="hidden" name="csrfmiddlewaretoken" value="{{csrf}}"><div class="mb-3"><label class="fw-bold small mb-1" style="color:#6E5039;">Reason for Declining (to notify client)</label><select name="reason_preset" class="form-select form-select-sm mb-2" onchange="if(this.value){document.getElementById('customReason{{b.id}}').value=this.value;}"><option value="">-- Select common reason or type below --</option><option value="Selected date is already booked / fully reserved.">Date already booked / fully reserved</option><option value="Date is outside our operating hours or artist schedule.">Date outside operating hours</option><option value="Location is outside our current service coverage area.">Location outside coverage area</option></select><textarea name="decline_reason" id="customReason{{b.id}}" class="form-control form-control-sm" rows="3" placeholder="e.g. This date has already been booked by another client. Please select another date." required></textarea></div><button type="submit" class="btn btn-danger w-100 rounded-pill fw-bold py-2"><i class="bi bi-send-fill"></i> Confirm Decline & Notify Client</button></form></div></div></div></div>{% endfor %}{% else %}<div class="text-center py-5"><div class="mb-3 fs-1 text-muted"><i class="bi bi-calendar-x"></i></div><h6 class="fw-bold" style="color:#523B29;">No customer reservations yet</h6><p class="text-muted small">Reservations booked by customers will appear here for review and acceptance.</p></div>{% endif %}</div></div></div></div>""" + SUPPORT_FOOTER_HTML + """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>"""

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
    discount_filter = request.GET.get('discount') == 'true'
    
    products=Product.objects.all()
    if discount_filter:
        products = [p for p in products if p.original_price and p.original_price > p.price]
    if q:
        products=[p for p in products if q.lower() in p.name.lower()]
    if cat!='All':
        products=[p for p in products if p.category == cat]
    if brand!='All':
        products=[p for p in products if p.brand == brand]
        
    html=render_template(HOME_HTML, {'products':products,'q':q,'cat':cat,'brand':brand, 'discount_filter':discount_filter}, request)
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
            if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
                msg = "This email address is already in use by another account."
            else:
                request.user.first_name = cd['full_name']
                request.user.email = new_email
                request.user.username = new_email
                
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
        
        customer_email = request.user.email
        customer_name = order.full_name
        current_manila_time = timezone.localtime(timezone.now(), MANILA_TZ)
        
        send_mail(
            subject=f"Order Confirmation (#{order.id}) - Belle's Couture",
            message=f"Hi {customer_name},\n\nThank you for your order with Belle's Couture! Your order (#{order.id}) has been successfully placed via Cash on Delivery on {current_manila_time.strftime('%B %d, %Y')}.\n\nDelivery Address: {order.address}\nTotal Amount: ₱{order.total_amount}\n\nWe will notify you once your order is processed and shipped.\n\nWarm regards,\nBelle's Couture Team",
            from_email=None,
            recipient_list=[customer_email],
            fail_silently=True,
        )
        
        send_mail(
            subject=f"New Product Order Placed (#{order.id}) - {customer_name}",
            message=f"A new order has been placed on Belle's Couture on {current_manila_time.strftime('%B %d, %Y')}!\n\nCustomer: {customer_name} ({customer_email})\nPhone: {order.phone}\nAddress: {order.address}\nTotal Amount: ₱{order.total_amount}\nPayment Method: Cash on Delivery\n\nPlease check your Artist Admin Hub to prepare items and update shipping status.",
            from_email=None,
            recipient_list=['artist@bellescouture.shop'],
            fail_silently=True,
        )

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
    error = None
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        req_date = request.POST['date']
        
        active_date_conflict = MakeupBooking.objects.filter(
            date=req_date,
            status__in=['Pending Approval', 'Accepted']
        ).exists()

        declined_date_conflict = False
        if not active_date_conflict:
            declined_bookings = MakeupBooking.objects.filter(
                date=req_date,
                status='Declined'
            )
            for db in declined_bookings:
                reason_lower = db.decline_reason.lower()
                if any(keyword in reason_lower for keyword in ['booked', 'reserved', 'unavailable', 'date', 'slot']):
                    declined_date_conflict = True
                    break

        if active_date_conflict or declined_date_conflict:
            error = f"The date {req_date} is already fully booked by another customer. Same date bookings are not allowed. Please choose a different date."
        else:
            booking = MakeupBooking.objects.create(
                user=request.user, 
                customer_name=request.POST['customer_name'], 
                email=request.POST['email'], 
                phone=request.POST['phone'], 
                service_type=request.POST['service_type'], 
                event_type=request.POST['event_type'], 
                date=req_date, 
                time=request.POST['time'], 
                address=request.POST['address'], 
                city=request.POST['city'], 
                additional_request=request.POST.get('additional_request', '')
            )
            current_manila_date_str = timezone.localtime(timezone.now(), MANILA_TZ).strftime('%B %d, %Y')
            success = f"Appointment booked successfully on {current_manila_date_str}!"
            
            send_mail(
                subject=f"Booking Confirmation: {booking.service_type} - Belle's Couture",
                message=f"Hi {booking.customer_name},\n\nYour appointment for {booking.service_type} on {booking.date} at {booking.time} has been received and is currently 'Pending Approval'.\n\nLocation: {booking.address}, {booking.city}\n\nWe will notify you once confirmed!\n\nWarm regards,\nBelle's Couture Team",
                from_email=None,
                recipient_list=[booking.email],
                fail_silently=True,
            )
            
            send_mail(
                subject=f"New Makeup Reservation: {booking.customer_name}",
                message=f"A new booking has been placed!\n\nClient: {booking.customer_name}\nService: {booking.service_type}\nDate: {booking.date} ({booking.time})\nCity: {booking.city}\n\nLog in to your Artist Admin Hub to review and accept this reservation.",
                from_email=None,
                recipient_list=['artist@bellescouture.shop'],
                fail_silently=True,
            )

    bookings = MakeupBooking.objects.filter(user=request.user).order_by('-created_at')
    
    all_bookings = MakeupBooking.objects.filter(status__in=['Pending Approval', 'Accepted'])
    taken_dates = set()
    
    for b in all_bookings:
        taken_dates.add(b.date.strftime('%Y-%m-%d'))
    
    for db in MakeupBooking.objects.filter(status='Declined'):
        if any(kw in db.decline_reason.lower() for kw in ['booked', 'reserved', 'unavailable', 'date', 'slot']):
            taken_dates.add(db.date.strftime('%Y-%m-%d'))

    booked_dates_json = json.dumps(list(taken_dates))
    today = timezone.localtime(timezone.now(), MANILA_TZ).date().isoformat()
    
    html = render_template(APPOINTMENT_HTML, {
        'bookings': bookings, 
        'success': success, 
        'error': error, 
        'today': today, 
        'booked_dates_json': booked_dates_json,
        'cat': 'All', 
        'brand': 'All', 
        'q': ''
    }, request)
    return HttpResponse(html)

def artist_admin_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    bookings = MakeupBooking.objects.all().order_by('-created_at')
    orders = Order.objects.all().order_by('-created_at')
    html = render_template(ARTIST_ADMIN_HTML, {'bookings': bookings, 'orders': orders, 'cat': 'All', 'brand': 'All', 'q': ''}, request)
    return HttpResponse(html)

def artist_admin_order_status(request, oid, status):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    try:
        o = Order.objects.get(id=oid)
        o.status = status
        o.save()
        
        send_mail(
            subject=f"Order Update (#{o.id}) - {status} - Belle's Couture",
            message=f"Hi {o.full_name},\n\nYour order (#{o.id}) status has been updated by our team to: {status}.\n\nThank you for shopping with Belle's Couture!",
            from_email=None,
            recipient_list=[o.user.email],
            fail_silently=True,
        )
    except:
        pass
    return HttpResponseRedirect('/artist-admin/')

def artist_admin_delete_order(request, oid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    try:
        o = Order.objects.get(id=oid)
        if o.status in ['Delivered', 'Cancelled']:
            o.delete()
    except:
        pass
    return HttpResponseRedirect('/artist-admin/')

def artist_admin_delete_booking(request, bid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    try:
        b = MakeupBooking.objects.get(id=bid)
        if b.status in ['Cancelled', 'Declined', 'Completed']:
            b.delete()
    except:
        pass
    return HttpResponseRedirect('/artist-admin/')

def artist_admin_status(request, bid, status):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    try:
        b = MakeupBooking.objects.get(id=bid)
        b.status = status
        if status == 'Cancelled':
            b.cancelled_at = timezone.now()
        b.save()
        
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

def artist_admin_decline(request, bid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        reason = request.POST.get('de_cline_reason', 'Selected date is unavailable or already booked.')
        try:
            b = MakeupBooking.objects.get(id=bid)
            b.status = 'Declined'
            b.decline_reason = reason
            b.cancelled_at = timezone.now()
            b.save()
            
            send_mail(
                subject=f"Reservation Update: Declined / Date Unavailable (#{b.id}) - Belle's Couture",
                message=f"Hi {b.customer_name},\n\nWe regret to inform you that your appointment for {b.service_type} on {b.date} could not be accommodated.\n\nReason / Note from Artist: {reason}\n\nYou are welcome to log in to your Belle's Couture account and book a different available date.\n\nWarm regards,\nBelle's Couture Team",
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
    html = render_template(AUTH_HTML, {'form': form, 'title': 'Welcome!', 'button': 'Login', 'footer': 'No account? <a href="/register/">Register</a> | <a href="/forgot-password/">Forgot Password?</a>', 'success_msg': success_msg}, request)
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
            
            reset_link = f"https://bellescouture.shop/reset-password/{token_str}/"
            
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
        if o.status == 'Cancelled' or o.status == 'Delivered':
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
        if b.status == 'Cancelled' or b.status == 'Declined':
            b.delete()
    except:
        pass
    return HttpResponseRedirect('/appointments/')

urlpatterns = [
    path('', home),
    path('product/<int:pid>/', product_detail),
    path('profile/', profile_view),
    path('register/', register_view),
    path('login/', login_value if 'login_value' in globals() else login_view),
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
    path('artist-admin/order-status/<int:oid>/<str:status>/', artist_admin_order_status),
    path('artist-admin/delete-order/<int:oid>/', artist_admin_delete_order),
    path('artist-admin/status/<int:bid>/<str:status>/', artist_admin_status),
    path('artist-admin/delete-booking/<int:bid>/', artist_admin_delete_booking),
    path('artist-admin/decline/<int:bid>/', artist_admin_decline),
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
        try:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE __main___makeupbooking ADD COLUMN decline_reason TEXT DEFAULT '';")
        except Exception:
            pass
    seed()
    # FORCE CREATE / UPDATE ARTIST ADMIN
    try:
        u = User.objects.filter(email='artist@bellescouture.shop').first()
        if u:
            u.is_staff = True
            u.is_superuser = True
            u.is_active = True
            u.set_password('admin123')
            u.save()
        else:
            artist_user = User.objects.create_superuser('artist@bellescouture.shop', 'artist@bellescouture.shop', 'admin123')
            artist_user.first_name = "Lead Makeup Artist"
            artist_user.save()
    except:
        pass
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

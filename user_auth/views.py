import pyotp
import json
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser

otp_store = {}  # Temporary storage (Use DB in production)

@csrf_exempt
def register_api(request):
    print("The register function is now running")
    if request.method == 'POST':
        data = json.loads(request.body)

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return JsonResponse({"error": "All fields are required"}, status=400)

        # Create user
        user = CustomUser.objects.create_user(username=username, email=email, password=password)

        # Generate OTP
        totp = pyotp.TOTP(pyotp.random_base32(), interval=300)
        otp = totp.now()

        # Store OTP temporarily
        otp_store[email] = {"otp": otp, "expires_at": datetime.now() + timedelta(minutes=5)}
        print(f"Generated OTP for {email}: {otp}")
        print(f"Current OTP Store: {otp_store}")
        # Send OTP via Email
        send_mail(
            'Email Verification OTP',
            f'Your OTP for email verification is: {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return JsonResponse({"message": "OTP sent", "user_id": user.id}, status=201)

    return JsonResponse({"error": "Invalid request"}, status=400)
@csrf_exempt
def verify_otp_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        email = data.get('email')
        user_otp = data.get('otp')

        if not email or not user_otp:
            print("❌ Missing email or OTP in request")
            return JsonResponse({"error": "Email and OTP are required"}, status=400)

        # Check if email exists in OTP store
        if email in otp_store:
            stored_data = otp_store[email]
            stored_otp = stored_data["otp"]


            # Verify OTP
            if str(stored_otp) == str(user_otp) and datetime.now() < stored_data["expires_at"]:
                del otp_store[email]  # OTP is one-time use
                print("✅ OTP verification successful")

                # Authenticate user and generate JWT
                from rest_framework_simplejwt.tokens import RefreshToken
                user = CustomUser.objects.get(email=email)
                refresh = RefreshToken.for_user(user)

                return JsonResponse({
                    "message": "OTP Verified",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }, status=200)

        print("❌ Invalid or expired OTP")
        return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

    print("❌ Invalid request method")
    return JsonResponse({"error": "Invalid request"}, status=400)
import random
import string

OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6


def generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))
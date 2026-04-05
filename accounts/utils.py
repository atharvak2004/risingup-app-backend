import secrets
import string
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_unique_username(first_name: str, birth_year: int):
    base = f"{first_name.lower()}{birth_year}"
    username = base
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    return username

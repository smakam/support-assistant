from jose import jwt
import secrets

# Generate a new secure random secret key
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"

print(f"New SECRET_KEY: {SECRET_KEY}")

data = {
    "sub": "demo_user",
    "role": "gamer"
}

token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
print(f"New token: {token}")
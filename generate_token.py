from jose import jwt

SECRET_KEY = "Qw1p8zX7vL2k9sT4bN6m3cR5yU0eJ2hV8fG4dS1aP7oW6lQ3"
ALGORITHM = "HS256"

data = {
    "sub": "demo_user",
    "role": "gamer"
}

token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
print(token)
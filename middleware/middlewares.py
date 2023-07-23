# middleware.py

import jwt
from flask import request, jsonify

# This is the secret key for decoding the JWT token.
# Keep this key secure and do not share it publicly.
secret_key = "chatbot"

def check_login_status(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "You have to login first"}), 401

        try:
            # Decode the JWT token and extract the user's email
            token_payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            email = token_payload.get("email")

            if not email:
                return jsonify({"message": "Invalid token"}), 401

            # Add the user's email to the request object for easy access in the protected route
            request.email = email
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return func(*args, **kwargs)

    return wrapper

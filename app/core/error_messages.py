from fastapi import HTTPException

class ErrorResponses:
    USER_EXISTS = HTTPException(
        status_code=409,
        detail="A user with this email already exists."
    )
    INVALID_CREDENTIALS = HTTPException(
        status_code=401,
        detail="Invalid email or password."
    )
    UNVERIFIED_EMAIL = HTTPException(
        status_code=403,
        detail="Email not verified. Please check your inbox."
    )
    INVALID_TOKEN = HTTPException(
        status_code=401,
        detail="Invalid or expired token."
    )
    USER_NOT_FOUND = HTTPException(
        status_code=404,
        detail="No account found with that email."
    )
    VALIDATION_ERROR = HTTPException(
        status_code=422,
        detail="Invalid request data."
    )
    INTERNAL_SERVER_ERROR = HTTPException(
        status_code=500,
        detail="Something went wrong on our end."
    )

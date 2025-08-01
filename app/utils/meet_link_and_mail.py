import random
from app.utils.email_utils import send_email

def generate_meet_link():
    return f"https://meet.google.com/{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=3))}-{'-'.join([''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=4)) for _ in range(2)])}"

async def send_meeting_email(email: str, booking_id: str):
    link = generate_meet_link()
    subject = "Booking Approved – Join Your Meeting"
    body = f"""
    Your booking (ID: {booking_id}) has been approved ✅

    Join your Google Meet: {link}

    Kindly be on time. Thank you.
    """
    send_email(email, subject, body)
    return link

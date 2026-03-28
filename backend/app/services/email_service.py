import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from pydantic import EmailStr

logger = logging.getLogger(__name__)

def get_mail_config():
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM_EMAIL or "noreply@hearth.local",
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
    )

async def send_invite_email(email_to: EmailStr, household_name: str, inviter_email: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"SMTP not configured. Skipping email to {email_to}")
        return
        
    html = f"""
    <h3>You have been invited to Hearth!</h3>
    <p><b>{inviter_email}</b> has invited you to join their household: <b>{household_name}</b>.</p>
    <p>Please register for an account using this email address ({email_to}) to accept the invitation.</p>
    <p><a href="{settings.FRONTEND_URL}/register" style="display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Join Household & Register</a></p>
    <p><small>If the button doesn't work, copy and paste this link: {settings.FRONTEND_URL}/register</small></p>
    """
    
    message = MessageSchema(
        subject="Invitation to join Hearth",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(get_mail_config())
    try:
        await fm.send_message(message)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

async def send_password_reset_email(email_to: EmailStr, token: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"SMTP not configured. Skipping password reset email to {email_to}")
        return
        
    reset_link = f"{settings.FRONTEND_URL}/login/reset?token={token}"
    html = f"""
    <h3>Password Reset Request</h3>
    <p>We received a request to reset the password for your Hearth account.</p>
    <p>If you made this request, click the button below to choose a new password. This link is only valid for 1 hour.</p>
    <br>
    <p><a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Reset Password</a></p>
    <br>
    <p><small>If you did not request a password reset, you can safely ignore this email.</small></p>
    <p><small>If the button doesn't work, copy and paste this link: {reset_link}</small></p>
    """
    
    message = MessageSchema(
        subject="Hearth Password Reset",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(get_mail_config())
    try:
        await fm.send_message(message)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

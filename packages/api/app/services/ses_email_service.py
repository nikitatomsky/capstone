"""AWS SES email service implementation for invitation delivery."""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SESEmailService:
    """AWS SES email service for sending invitation emails."""

    def __init__(self, region_name: str | None = None):
        """
        Initialize SES client.

        Args:
            region_name: AWS region for SES (defaults to AWS_REGION env var or us-east-1)
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.ses_client = boto3.client("ses", region_name=self.region_name)

        # Configuration
        self.from_email = os.getenv("SES_FROM_EMAIL", "noreply@example.com")

        # Parse configuration set name (strip comments and whitespace)
        config_set_raw = os.getenv("SES_CONFIGURATION_SET", "").strip()
        # Only use if it's a valid name (not empty, not a comment)
        self.configuration_set = None
        if config_set_raw and not config_set_raw.startswith("#"):
            self.configuration_set = config_set_raw

        logger.info(
            f"Initialized SESEmailService (region: {self.region_name}, "
            f"from: {self.from_email})"
        )

    async def send_telegram_invitation(
        self,
        email: str,
        technician_name: str,
        telegram_link: str,
    ) -> bool:
        """
        Send Telegram invitation via email using AWS SES.

        Args:
            email: Recipient email address
            technician_name: Technician's name for personalization
            telegram_link: Telegram deeplink with invitation token

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Connect Your Telegram Account - Field Intake Service"

        # HTML email body
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Hi {technician_name},</h2>
            <p>You've been invited to connect your Telegram account to the Field Intake Service.</p>
            <p>Click the button below to get started:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{telegram_link}"
                   style="background-color: #0088cc; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Connect Telegram Account
                </a>
            </p>
            <p><strong>Or copy and paste this link:</strong><br>
            <a href="{telegram_link}">{telegram_link}</a></p>
            <p><em>This invitation link expires in 1 hour.</em></p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                If you did not request this invitation, please ignore this email.
            </p>
        </body>
        </html>
        """

        # Plain text fallback
        text_body = f"""
Hi {technician_name},

You've been invited to connect your Telegram account to the Field Intake Service.

Click this link to get started:
{telegram_link}

This invitation link expires in 1 hour.

If you did not request this invitation, please ignore this email.
        """

        try:
            # Prepare email parameters
            email_params = {
                "Source": self.from_email,
                "Destination": {
                    "ToAddresses": [email]
                },
                "Message": {
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Text": {
                            "Data": text_body,
                            "Charset": "UTF-8"
                        },
                        "Html": {
                            "Data": html_body,
                            "Charset": "UTF-8"
                        }
                    }
                }
            }

            # Add configuration set if specified
            if self.configuration_set:
                email_params["ConfigurationSetName"] = self.configuration_set

            # Send email
            response = self.ses_client.send_email(**email_params)

            message_id = response.get("MessageId")
            logger.info(
                f"Email sent successfully to {email} "
                f"(MessageId: {message_id})"
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                f"Failed to send email to {email}: [{error_code}] {error_message}",
                exc_info=True
            )

            # Common SES errors
            if error_code == "MessageRejected":
                logger.error(
                    f"Email rejected by SES. Check that {self.from_email} is verified "
                    "and account is out of sandbox mode for production use."
                )
            elif error_code == "MailFromDomainNotVerified":
                logger.error(
                    f"Domain not verified. Verify {self.from_email} in SES console."
                )

            return False

        except Exception as e:
            logger.error(
                f"Unexpected error sending email to {email}: {e}",
                exc_info=True
            )
            return False

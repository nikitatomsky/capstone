"""AWS SNS SMS service implementation."""
import logging

import boto3
from botocore.exceptions import ClientError

from app.services.sms_service import SMSService

logger = logging.getLogger(__name__)


class SNSSMSService(SMSService):
    """AWS SNS SMS service."""

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize SNS client.

        Args:
            region_name: AWS region for SNS
        """
        self.sns_client = boto3.client("sns", region_name=region_name)

    async def send_telegram_invitation(
        self,
        phone_number: str,
        technician_name: str,
        telegram_link: str,
    ) -> bool:
        """Send SMS via AWS SNS."""
        message = (
            f"Hi {technician_name}, tap this link to connect your "
            f"Telegram account to Field Intake:\n\n"
            f"{telegram_link}\n\n"
            f"This link expires in 1 hour."
        )

        try:
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": "FieldIntake"
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional"
                    }
                }
            )

            message_id = response.get("MessageId")
            logger.info(
                f"SMS sent successfully to {phone_number} "
                f"(MessageId: {message_id})"
            )
            return True

        except ClientError as e:
            logger.error(
                f"Failed to send SMS to {phone_number}: {e}",
                exc_info=True
            )
            return False

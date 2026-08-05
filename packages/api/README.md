# Field Intake Service - Backend API

FastAPI backend for the Field Intake Service, providing conversational intake through Telegram Bot API.

## Environment Variables

### Telegram Bot Configuration

- `TELEGRAM_BOT_TOKEN`: Your bot's token from BotFather (for local development)
- `TELEGRAM_BOT_USERNAME`: Your bot's username (e.g., `my_field_bot`)
- `TELEGRAM_BOT_TOKEN_SECRET_NAME`: AWS Secrets Manager secret name (for production)
- `TELEGRAM_INVITATION_TTL_SECONDS`: Invitation expiration in seconds (default: 3600)

### AWS Configuration

- `AWS_REGION`: AWS region for DynamoDB and Secrets Manager (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID`: AWS access key (for local development)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (for local development)
- `AWS_DEFAULT_REGION`: AWS default region

### SMS Configuration (Issue #37)

- `USE_AWS_SNS`: Set to `true` to enable AWS SNS for SMS (default: `false`)
- `AWS_SNS_SENDER_ID`: Optional SMS sender ID (default: `FieldIntake`)

**Local Development**: Uses `FakeSMSService` (logs messages instead of sending)
**Production**: Uses `SNSSMSService` (sends real SMS via AWS SNS)

### LLM Configuration

- `ANTHROPIC_API_KEY`: API key for Claude (Anthropic) LLM service

## Local Development vs Production

### Local Development

**Bot Token**: Use `TELEGRAM_BOT_TOKEN` from `.env` file
- Copy `.env.example` to `.env`
- Add your Telegram bot token
- Token read directly from environment variable

**Database**: Can use DynamoDB Local or AWS DynamoDB
- AWS DynamoDB recommended for testing invitation system
- Requires AWS credentials configured

### Production

**Bot Token**: Read from AWS Secrets Manager
- Token stored securely in Secrets Manager
- Retrieved at runtime using IAM permissions
- Environment variable `TELEGRAM_BOT_TOKEN_SECRET_NAME` specifies secret path

**Database**: AWS DynamoDB only
- Production tables in AWS
- Lambda execution role provides access

## Setup

1. **Install dependencies**:
   ```bash
   cd packages/api
   poetry install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Verify AWS access** (for invitation system):
   ```bash
   # Test Secrets Manager access
   aws secretsmanager get-secret-value \
     --secret-id field-intake/dev/telegram-bot-token

   # Test DynamoDB access
   aws dynamodb describe-table \
     --table-name field-intake-telegram-invitations-dev
   ```

4. **Run local server**:
   ```bash
   poetry run uvicorn app.main:app --reload --port 4000
   ```

5. **Expose webhook with ngrok** (separate terminal):
   ```bash
   ngrok http 4000
   ```

6. **Register webhook**:
   ```bash
   curl -F "url=https://<ngrok-id>.ngrok.io/webhook" \
     https://api.telegram.org/bot<TOKEN>/setWebhook
   ```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_webhook.py
```

## Dependencies

- **boto3**: AWS SDK for Secrets Manager and DynamoDB
- **FastAPI**: Web framework for API endpoints
- **python-telegram-bot**: Telegram Bot API client
- **anthropic**: Claude LLM integration
- **pydantic**: Data validation and schemas

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── models/                 # Pydantic models
│   ├── telegram.py         # Telegram webhook payloads
│   ├── intake.py           # Intake record schemas
│   ├── assignment.py       # Assignment workflows
│   └── technician.py       # Technician models
├── routers/                # API route handlers
│   ├── webhook.py          # Telegram webhook endpoint
│   ├── health.py           # Health check
│   ├── assignment.py       # Assignment CRUD
│   └── technician.py       # Technician CRUD
├── services/               # Business logic
│   ├── extraction_service.py  # LLM-powered extraction
│   ├── session_service.py     # Conversation state management
│   └── telegram_client.py     # Telegram API client
└── repositories/           # Data access layer
    ├── assignment_repository.py
    └── technician_repository.py
```

## IAM Permissions

For local development, attach the Terraform-managed IAM policy to your user:

```bash
cd infra/stacks/dev
terraform output telegram_backend_policy_arn

aws iam attach-user-policy \
  --user-name YOUR_IAM_USER \
  --policy-arn $(terraform output -raw telegram_backend_policy_arn)
```

See `infra/modules/iam/README.md` for details on permissions granted.

## AWS SNS Configuration for SMS (Issue #37)

### Local Development

By default, uses `FakeSMSService` which logs messages instead of sending.

Set `USE_AWS_SNS=false` in `.env`.

### Production Setup

1. **Enable AWS SNS**:
   ```bash
   export USE_AWS_SNS=true
   export AWS_REGION=us-east-1
   ```

2. **Configure IAM permissions**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "sns:Publish"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Test SMS sending**:
   ```bash
   curl -X POST http://localhost:4000/api/technicians/{id}/telegram-invitation
   ```

### SMS Message Format

```
Hi {name}, tap this link to connect your Telegram account to Field Intake:
https://t.me/{bot_username}?start={token}

This link expires in 1 hour.
```

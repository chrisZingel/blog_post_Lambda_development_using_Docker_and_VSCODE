import pytest
import json
from unittest.mock import patch, MagicMock
from src.email_attachment_handler import EmailAttachmentHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# === FIXTURES ===

@pytest.fixture
def mock_event():
    return {
        "Records": [{
            "s3": {
                "object": {
                    "key": "folder/Test:Invoice<>.pdf"
                }
            }
        }]
    }

@pytest.fixture
def mock_context():
    return {}

@pytest.fixture
def mock_config():
    return {
        "aws_region": "us-west-1",
        "bucket_name": "test-bucket",
        "subject": "Subject",
        "from_email": "from@example.com",
        "to_email": "to@example.com"
    }


# === TESTS ===

@patch("builtins.open")
@patch("json.load")
def test_init(mock_json_load, mock_open, mock_event, mock_context, mock_config):
    mock_json_load.return_value = mock_config
    handler = EmailAttachmentHandler(mock_event, mock_context)
    assert handler.config["bucket_name"] == "test-bucket"
    assert handler.event == mock_event


@patch("builtins.open")
@patch("json.load")
def test_sanitize_email_filename(mock_json_load, mock_open, mock_event, mock_context):
    mock_json_load.return_value = {}
    handler = EmailAttachmentHandler(mock_event, mock_context)
    unsafe = 'Inv:<>*?"/.pdf'
    sanitized = handler.sanitize_email_filename(unsafe)
    assert sanitized == 'Inv_______.pdf'


@patch("builtins.open")
@patch("json.load")
def test_retrieve_first_key(mock_json_load, mock_open, mock_event, mock_context):
    mock_json_load.return_value = {}
    handler = EmailAttachmentHandler(mock_event, mock_context)
    handler.retrive_first_key()
    assert handler.first_key == "folder/Test:Invoice<>.pdf"


@patch("boto3.client")
@patch("builtins.open")
@patch("json.load")
def test_fetch_s3_object(mock_json_load, mock_open, mock_boto3, mock_event, mock_context, mock_config):
    mock_json_load.return_value = mock_config
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"file-data")}
    mock_boto3.return_value = mock_s3

    handler = EmailAttachmentHandler(mock_event, mock_context)
    handler.retrive_first_key()
    handler.fetch_s3_object()

    mock_s3.get_object.assert_called_once_with(
        Bucket="test-bucket", Key=handler.first_key
    )
    assert handler.s3_object["Body"].read() == b"file-data"


@patch("builtins.open")
@patch("json.load")
def test_compose_email(mock_json_load, mock_open, mock_event, mock_context, mock_config):
    mock_json_load.return_value = mock_config
    handler = EmailAttachmentHandler(mock_event, mock_context)
    handler.first_key = "folder/file name.txt"
    mock_body = MagicMock()
    mock_body.read.return_value = b"some-content"

    handler.s3_object = {"Body": mock_body}
    handler.compose_email()

    msg = handler.msg
    assert isinstance(msg, MIMEMultipart)
    assert "file name.txt" in msg.as_string()

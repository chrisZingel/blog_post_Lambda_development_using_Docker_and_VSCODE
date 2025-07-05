import json
import logging
import re
import unicodedata
import urllib.parse
import boto3

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError



class EmailAttachmentHandler:
    def __init__(self, event, context):
        with open('src/config.json') as f:
            self.config = json.load(f)

        self.event = event
        self.context = context
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def sanitize_email_filename(self, name, replacement="_"):
        name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name).strip().strip(".")
        return name[:255]

    def process_event(self):
        try:
            self.retrive_first_key()
            self.fetch_s3_object()
            self.compose_email()
            self.send_email()
        except ClientError as e:
            self.logger.error(f"AWS ClientError: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        else:
            self.logger.info("Email sent successfully")
            return {
                "statusCode": 200,
                "body": json.dumps("Email sent successfully!")
            }


    def retrive_first_key(self):
        record = self.event["Records"][0]
        key = record["s3"]["object"]["key"]
        self.first_key = urllib.parse.unquote_plus(key)
        self.logger.info(f"Retrieved key: {self.first_key}")

    def fetch_s3_object(self):
        s3 = boto3.client("s3", region_name=self.config["aws_region"])
        self.s3_object = s3.get_object(
            Bucket=self.config["bucket_name"],
            Key=self.first_key
        )

    def compose_email(self):
        file_content = self.s3_object["Body"].read()
        filename = self.first_key.split("/")[-1]
        sanitized_filename = self.sanitize_email_filename(filename)

        msg = MIMEMultipart()
        msg["Subject"] = self.config["subject"]
        msg["From"] = self.config["from_email"]
        msg["To"] = self.config["to_email"]
        msg.attach(MIMEText(f"Please find attached the file: {filename}", "plain"))

        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(file_content)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", f'attachment; filename="{sanitized_filename}"')
        msg.attach(attachment)

        self.msg = msg

    def send_email(self):
        ses = boto3.client("ses", region_name=self.config["aws_region"])
        response = ses.send_raw_email(
            Source=self.config["from_email"],
            Destinations=[self.config["to_email"]],
            RawMessage={"Data": self.msg.as_string()}
        )
        self.logger.info(f"SES response: {response}")
        return response
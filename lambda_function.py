from src.email_attachment_handler import EmailAttachmentHandler

def handler(event, context): 
    return EmailAttachmentHandler(event, context).process_event()

# Only runs in local testing (e.g. from VSCode)
if __name__ == "__main__":
    import json

    # Load test event
    with open("test_event.json") as f:
        test_event = json.load(f)

    # Run the Lambda handler with dummy context
    result = handler(test_event, context={})
    print(result)

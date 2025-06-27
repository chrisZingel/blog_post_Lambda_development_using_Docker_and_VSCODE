# Image used by AWS for lambda python
FROM public.ecr.aws/lambda/python:3.13

# Add tar used by VSCode
RUN dnf install -y tar gzip \
 && dnf clean all

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# or copy all code from a  directory
COPY src/ ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]
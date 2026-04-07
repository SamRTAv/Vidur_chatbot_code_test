# # Use python 3.9 or 3.10
# FROM python:3.12

# # Set the working directory
# WORKDIR /code

# # Copy the requirements file
# COPY ./requirements.txt /code/requirements.txt

# # Install dependencies (No cache to save space, though HF has 16GB)
# RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# # Copy the rest of your code
# COPY . /code

# # Create a non-root user (Hugging Face Security Requirement)
# RUN useradd -m -u 1000 user
# USER user
# ENV HOME=/home/user \
# 	PATH=/home/user/.local/bin:$PATH

# # Expose port 7860 (Hugging Face specific port)
# EXPOSE 7860

# # Start the app on port 7860
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]



# 1. Use Python 3.12 as requested
FROM python:3.12

# 2. Set working directory
WORKDIR /code

# 3. Create the user 1000 FIRST
# Hugging Face Spaces run as user 1000 by default. We create it explicitly here.
RUN useradd -m -u 1000 user

# 4. Copy requirements and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. FIX PERMISSIONS (The Critical Step)
# We create the empty folders for your databases and give 'user' full ownership.
# This prevents the "Permission Denied" error when the app tries to write to them.
RUN mkdir -p /code/chroma_db_Ayurveda \
             /code/chroma_db_Lifestyle \
             /code/chroma_db_Mental_health \
             /code/chroma_db_Yoga \
             /code/chroma_db_psychology && \
    chown -R user:user /code

# 6. Copy the rest of your code
# We use '--chown=user' so the copied files belong to the user, not root.
COPY --chown=user . /code

# 7. Switch to the non-root user for security
USER user

# 8. Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 9. Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
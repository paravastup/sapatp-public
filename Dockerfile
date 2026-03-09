FROM ubuntu:18.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.6 and other dependencies
RUN apt-get update && apt-get install -y \
    python3.6 \
    python3.6-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    build-essential \
    libssl-dev \
    libffi-dev \
    default-libmysqlclient-dev \
    libpq-dev \
    netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python and pip
RUN ln -sf /usr/bin/python3.6 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# Set up working directory
WORKDIR /app

# Copy the nwrfcsdk library
COPY nwrfcsdk /usr/nwrfcsdk

# Set environment variables for nwrfcsdk
ENV LD_LIBRARY_PATH=/usr/nwrfcsdk/lib:$LD_LIBRARY_PATH
ENV SAPNWRFC_HOME=/usr/nwrfcsdk

# Copy the application code
COPY atp /app
COPY requirements.txt /app/
COPY pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl /app/

# Install pyrfc wheel and other dependencies
RUN pip install --upgrade pip \
    && pip install /app/pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl \
    && pip install -r requirements.txt \
    && pip install mysqlclient gunicorn djangorestframework djangorestframework-jwt

# Create necessary directories
RUN mkdir -p /app/sock /var/log/gunicorn \
    && chmod 777 /app/sock /var/log/gunicorn

# Expose port for the application
EXPOSE 8000

# Start the application
CMD bash -c "echo 'Waiting for MySQL...' && while ! nc -z db 3306; do sleep 1; done && echo 'MySQL started' && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 --timeout 120 --workers 2 atp.wsgi:application"
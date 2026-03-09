FROM python:3.9

# Set the working directory
WORKDIR /var/www/atp/atp/

ENV LD_LIBRARY_PATH /usr/nwrfcsdk:/usr/nwrfcsdk/lib:/usr/nwrfcsdk/lib:/usr/nwrfcsdk

# Copy the app code
COPY . .

COPY /usr/nwrfcsdk /usr/nwrfcsdk


# Install the wheel file
RUN pip install pyrfc

# Install the app dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set environment variables
# SECRET_KEY must be provided via environment variable or .env file
# ENV SECRET_KEY='your-secret-key-here'

# Create a directory for the socket file and change the ownership
RUN mkdir /var/www/atp/atp/sock
RUN chown -R www-data:www-data /var/www/atp/atp/sock

# Copy the nginx configuration file
COPY projectdirectory.conf /etc/nginx/conf.d/

# Copy the static files
COPY app/static /var/www/atp/atp/static

# Expose the port for nginx
EXPOSE 80

# Start the nginx and gunicorn servers
CMD ["/bin/bash", "-c", "/usr/sbin/nginx -g 'daemon off;' && gunicorn --bind unix:/var/www/atp/atp/sock/atp.sock atp.wsgi:application"]

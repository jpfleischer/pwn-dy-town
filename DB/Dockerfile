# Use Alpine-based MariaDB image for ARM-compatible systems
FROM yobasystems/alpine-mariadb:latest

# Set environment variables for MariaDB
ENV MYSQL_ROOT_PASSWORD=rootpassword
ENV MYSQL_DATABASE=mydatabase
ENV MYSQL_USER=myuser
ENV MYSQL_PASSWORD=mypassword

# Expose the default MariaDB port
EXPOSE 3306

# Copy the SQL script into the Docker container
COPY script.sql /docker-entrypoint-initdb.d/


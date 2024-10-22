# Use the official MySQL image from the Docker Hub
FROM mysql:latest

# Set environment variables for MySQL
ENV MYSQL_ROOT_PASSWORD=rootpassword
ENV MYSQL_DATABASE=mydatabase
ENV MYSQL_USER=myuser
ENV MYSQL_PASSWORD=mypassword

# Expose the default MySQL port
EXPOSE 3306

# Copy the SQL script into the Docker container
COPY script.sql /docker-entrypoint-initdb.d/

# Add a custom configuration file if needed
# COPY my.cnf /etc/mysql/my.cnf

# Run the MySQL server
CMD ["mysqld"]
run: stop
	-docker network create ponynetwork
	docker build -t db-image .
	docker run --platform linux/arm64/v8 --name db -v mysql-data:/var/lib/mysql \
	--network=ponynetwork \
	-p 3306:3306 -d db-image

stop down:
	-docker stop db
	-docker rm db

shell:
	docker exec -it db bash

logs:
	docker logs db

exec-script:
	docker exec -it db //bin//bash -c "mysql -u root -prootpassword mydatabase < /docker-entrypoint-initdb.d/script.sql"

clean: stop
	-docker volume rm mysql-data

# New recipe to query the SQL database:
query:
	@echo "Displaying all rows from 'messages' table..."
	docker exec -it db /bin/sh -c "mysql -u root -prootpassword -e 'SELECT * FROM messages;' mydatabase"


dump:
	@echo "Dumping database 'mydatabase' to file 'db_dump.sql'..."
	docker exec db /bin/sh -c "mysqldump -u root -prootpassword mydatabase" > db_dump.sql
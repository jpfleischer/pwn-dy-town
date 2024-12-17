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

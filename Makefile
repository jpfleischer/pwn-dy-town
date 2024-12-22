# Makefile for pwn-scraper

run: stop build
	docker run \
		--name pwn-scraper \
		-p 5900:5900 \
		-v ${CURDIR}/cookies.json:/app/cookies.json \
		-v ${CURDIR}/pony-town-settings.json:/app/pony-town-settings.json \
		-v "${CURDIR}/overlay/input_grabs:/app/overlay/input_grabs" \
		--network=ponynetwork \
		-d pwn-scraper

	make logs

build:
	docker build -t pwn-scraper .

stop down:
	-@docker stop pwn-scraper 2>/dev/null || true
	-@docker rm pwn-scraper 2>/dev/null || true
	-@docker-compose down 2>/dev/null || true

logs:
	docker logs -f pwn-scraper

shell:
	docker exec -it `docker ps -aqf "ancestor=pwn-scraper"` bash
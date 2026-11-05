build:
	docker compose build
save:
	docker image save -o callerBot.tar caller_bot
load:
	docker image load -i callerBot.tar
run:
	docker compose up -d
stop:
	docker compose stop
logs:
	docker compose logs -f
rmc:
	docker compose down
dev-run:
	docker compose up --build
dev-stop:
	docker compose down
replace:
	docker compose down
	docker rmi caller_bot
	docker image load -i callerBot.tar
	docker compose up -d --no-build

build:
	docker build -t caller_bot .
save:
	docker image save -o callerBot.tar caller_bot
load:
	docker image load -i callerBot.tar
run:
	docker run -d --env-file .env --name callerBot caller_bot
stop:
	docker stop callerBot
logs:
	docker logs callerBot
rmc:
	docker rm callerBot
dev-run:
	docker build -t caller_bot .
	docker run --env-file .env --name callerBot --rm caller_bot
dev-stop:
	docker stop callerBot
	docker rm callerBot
replace:
	docker stop callerBot
	docker rm callerBot
	docker rmi caller_bot
	docker image load -i callerBot.tar
	docker run -d --env-file .env --name callerBot caller_bot
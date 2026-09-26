.PHONY: up down reset etl test dashboard logs

up:
	docker compose up -d postgres dashboard

down:
	docker compose down

reset:
	docker compose down -v

etl:
	docker compose --profile tools run --rm etl python -m src.main

test:
	docker compose --profile tools run --rm etl pytest -v

dashboard:
	docker compose up -d dashboard

logs:
	docker compose logs -f --tail=100

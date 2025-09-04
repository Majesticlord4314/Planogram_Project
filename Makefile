# Simple dev shortcuts

.PHONY: backend frontend all stop restart

backend:
	bash scripts/start-backend.sh

frontend:
	bash scripts/start-frontend.sh

all:
	@echo "Starting backend in background and frontend in foreground..."
	( bash scripts/start-backend.sh & ) ; bash scripts/start-frontend.sh

stop:
	@echo "Stopping frontend and backend..."
	bash scripts/stop-frontend.sh || true
	bash scripts/stop-backend.sh || true

restart: stop
	@echo "Restarting both servers..."
	( bash scripts/start-backend.sh & ) ; bash scripts/start-frontend.sh


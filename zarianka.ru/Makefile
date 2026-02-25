# Zarianka Pots — Build & Deploy
# ─────────────────────────────────────────────────────────────
# Deployment target: nginx on my_server (95.216.27.23)
# Override any variable: make deploy SERVER=other_host

SERVER      ?= my_server
DEPLOY_USER ?= raeno
DEPLOY_PATH ?= /var/www/zarianka.ru
DIST_DIR    := dist/

.PHONY: all dev build deploy release clean help

## Default target
all: build

## Start local development server
dev:
	mise exec -- npm run dev

## Build production site into ./dist
build:
	mise exec -- npm run build

## Deploy ./dist to nginx server via rsync
deploy:
	@echo "→ Deploying to $(SERVER):$(DEPLOY_PATH) ..."
	rsync -avz --delete \
		--exclude '.DS_Store' \
		$(DIST_DIR) $(DEPLOY_USER)@$(SERVER):$(DEPLOY_PATH)/
	@echo "✓ Done — https://zarianka.ru"

## Build then deploy in one step
release: build deploy

## Remove build output
clean:
	rm -rf $(DIST_DIR)

## Show available targets
help:
	@echo ""
	@echo "  make dev       – start dev server (localhost:4321)"
	@echo "  make build     – production build → ./dist"
	@echo "  make deploy    – rsync ./dist to $(SERVER):$(DEPLOY_PATH)"
	@echo "  make release   – build + deploy"
	@echo "  make clean     – remove ./dist"
	@echo ""
	@echo "  Override vars:  make deploy SERVER=other_host DEPLOY_PATH=/srv/www/zarianka.ru"
	@echo ""

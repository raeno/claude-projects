UNAME_M := $(shell uname -m)
UNAME_S := $(shell uname -s)

# Auto-detect backend: Apple Silicon → mlx, everything else → cpu
ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    BACKEND ?= mlx
  else
    BACKEND ?= cpu
  endif
else
  BACKEND ?= cpu
endif

.PHONY: install install-dev install-bot test lint format bot clean

install:
	uv sync --extra $(BACKEND)
	@echo "Installed with backend: $(BACKEND)"

install-dev:
	uv sync --extra $(BACKEND) --extra dev
	@echo "Installed with backend: $(BACKEND) + dev"

test:
	uv run pytest -v

lint:
	uv run ruff check podcast2obsidian/ tests/

format:
	uv run ruff format podcast2obsidian/ tests/

install-bot:
	uv sync --extra cpu --extra bot --extra dev
	@echo "Installed with cpu + bot + dev"

bot:
	uv run python -m podcast2obsidian.bot

clean:
	rm -rf .venv dist *.egg-info

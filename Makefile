REMAINING_GOALS = $(filter-out clean lint lint-strict install,$(MAKECMDGOALS))

ifeq ($(MAKECMDGOALS),)
    REMAINING_GOALS = all
endif

ifneq ($(REMAINING_GOALS),)
    ifeq ($(MAP),)
        $(error MAP variable is required to use target $(REMAINING_GOALS). Usage: make MAP=path/to/map.txt)
    endif
endif

all: install lint run

install:
	@pip install poetry || python3 -m pip install poetry || (echo "Error: Poetry installation failed. Please install Poetry manually." && exit 1)
	@echo "Installing dependencies..."
	@poetry install

run:
	@echo "Running the simulation...\n"
	@PYGAME_HIDE_SUPPORT_PROMPT=1 poetry run python main.py $(MAP)

lint:
	@echo "Running linters..."
	@poetry run flake8 .
	@poetry run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "Running linters in strict mode..."
	@poetry run flake8 .
	@poetry run mypy . --strict

debug:
	@echo "Running the simulation in debug mode...\n"
	@PYGAME_HIDE_SUPPORT_PROMPT=1 poetry run python -m pdb main.py $(MAP)

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" | xargs rm -rf
	@rm -rf *.lock .mypy_cache

.PHONY: install run lint lint-strict debug clean

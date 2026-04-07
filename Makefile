.PHONY: install skill

MODE ?= global

install:
	@if [ "$(MODE)" = "local" ]; then \
		test -n "$(REPO)" || { echo "REPO=/abs/path/to/repo is required for MODE=local" >&2; exit 1; }; \
		python3 scripts/setup_main.py local "$(REPO)" $(if $(LOCALE),--locale "$(LOCALE)"); \
	elif [ "$(MODE)" = "global" ]; then \
		python3 scripts/setup_main.py global $(if $(LOCALE),--locale "$(LOCALE)"); \
	else \
		echo "Unsupported MODE=$(MODE). Use MODE=global or MODE=local" >&2; \
		exit 1; \
	fi

skill:
	@true

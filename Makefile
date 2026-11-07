# rdx — developer and CI entry points (CLAUDE.md "Commands", MISSION §7).
#
# `make check` is the fast gate run before every commit and by ci.yml. CI runs exactly these targets and the
# pnpm scripts they call; nothing else is assumed. Every target fails loudly when its tool or input is missing:
# nothing here fakes green.

SHELL := bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --no-builtin-rules --no-print-directory

# ---- variables -------------------------------------------------------------------------------------------
CARGO ?= cargo
PNPM ?= pnpm
UI_DIR ?= ui
# `make parity FILTER=<api package or spec class>` (forwarded to scripts/parity.sh --filter).
FILTER ?=
# `make fuzz TARGET=<fuzz target>`.
TARGET ?=
# Optional pass-throughs for `make parity`: PARITY_TARGET is read by scripts/parity.sh from the environment.
PARITY_TARGET ?=
TASK ?=
OUT ?=
# Cargo honors CARGO_TERM_COLOR from the environment; default to auto when unset.
CARGO_TERM_COLOR ?= auto
export CARGO_TERM_COLOR
export PARITY_TARGET

# Runs a pnpm script inside ui/, installing dependencies first when node_modules is missing.
define ui_run
cd "$(UI_DIR)" && { [[ -d node_modules ]] || $(PNPM) install --frozen-lockfile; } && $(PNPM) $(1)
endef

.PHONY: help check fmt fmt-check clippy test doc deny audit \
        ui-install ui-lint ui-test ui-build e2e \
        oracle-up oracle-down parity bench fuzz

# ---- gates -------------------------------------------------------------------------------------------------
help: ## List the available targets
	@echo "rdx — make targets"
	@echo
	@awk 'BEGIN { FS = ":.*## " } /^[a-zA-Z0-9_-]+:.*## / { printf "  %-12s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo
	@echo "variables: FILTER=<api package or spec class> (parity), TARGET=<fuzz target> (fuzz),"
	@echo "           PARITY_TARGET=legacy|rdx TASK=<gradle task> OUT=<report path> (parity), CARGO_TERM_COLOR"

check: fmt-check clippy test deny audit ui-lint ui-test ## Fast gate: fmt, clippy -D warnings, tests, deny, audit, UI lint + tests

fmt: ## Format the Rust workspace
	$(CARGO) fmt --all

fmt-check: ## Fail if the Rust workspace is not formatted
	$(CARGO) fmt --all --check

clippy: ## Clippy on every target and feature, warnings are errors
	$(CARGO) clippy --workspace --all-targets --all-features -- -D warnings

test: ## Run the Rust tests with nextest (a crate without tests passes)
	$(CARGO) nextest run --workspace --no-tests=pass

doc: ## Build the API docs; warnings (e.g. missing docs) are errors
	RUSTDOCFLAGS="-D warnings" $(CARGO) doc --workspace --no-deps

deny: ## Licenses, bans, sources and advisories (deny.toml)
	$(CARGO) deny check

audit: ## RustSec advisories against Cargo.lock
	$(CARGO) audit

# ---- frontend (ui/, owned by the UI scaffold; scripts defined in ui/package.json) --------------------------
ui-install: ## pnpm install --frozen-lockfile in ui/
	cd "$(UI_DIR)" && $(PNPM) install --frozen-lockfile

ui-lint: ## eslint + prettier --check + vue-tsc in ui/
	$(call ui_run,lint)

ui-test: ## vitest run in ui/
	$(call ui_run,test)

ui-build: ## Production build of the SPA (vue-tsc + vite build)
	$(call ui_run,build)

e2e: ## Playwright journeys + screenshots into docs/ui-review/
	$(call ui_run,e2e)

# ---- oracle and parity (scripts owned by the CI scaffold) -----------------------------------------------------
oracle-up: ## Start legacy Rundeck 6.3.0 in Docker (scripts/oracle.sh up)
	bash scripts/oracle.sh up

oracle-down: ## Stop the legacy oracle (scripts/oracle.sh down)
	bash scripts/oracle.sh down

# Only the options that were given are forwarded; scripts/parity.sh applies its own defaults (target rdx, task apiTest).
PARITY_ARGS := $(if $(FILTER),--filter "$(FILTER)") $(if $(PARITY_TARGET),--target "$(PARITY_TARGET)") \
               $(if $(TASK),--task "$(TASK)") $(if $(OUT),--out "$(OUT)")

parity: ## Upstream functional tests against rdx (or legacy): make parity FILTER=<ApiSpecName>
	bash scripts/parity.sh $(strip $(PARITY_ARGS))

bench: ## Benchmarks (scripts/bench/run.sh)
	bash scripts/bench/run.sh

fuzz: ## Fuzz one target for 60 s: make fuzz TARGET=<name>
	@[[ -n "$(TARGET)" ]] || { echo "usage: make fuzz TARGET=<fuzz target>" >&2; exit 2; }
	$(CARGO) +nightly fuzz run $(TARGET) -- -max_total_time=60

# CoralCon — judge-facing shortcuts
# Usage: make judge | make verify | make serve | make pack | make real

PY ?= python

.PHONY: help judge verify serve pack real benchmark proof install

help:
	@echo "CoralCon make targets:"
	@echo "  make install    Install dependencies"
	@echo "  make judge      Run the deterministic sample judge demo + proof"
	@echo "  make verify     10-second pass/fail verification checklist"
	@echo "  make benchmark  Cold vs cached Coral cache benchmark"
	@echo "  make proof      Print the Coral SQL proof report"
	@echo "  make pack       Generate the submission pack"
	@echo "  make serve      Launch the web dashboard at :8000"
	@echo "  make real       Run the demo against real Coral (needs CORAL_AVAILABLE=true)"

install:
	$(PY) -m pip install -r requirements.txt

judge:
	$(PY) -m coralcon.cli judge-demo --sample
	$(PY) -m coralcon.cli proof

verify:
	$(PY) -m coralcon.cli verify

benchmark:
	$(PY) -m coralcon.cli benchmark-cache --sample

proof:
	$(PY) -m coralcon.cli proof

pack:
	$(PY) -m coralcon.cli submit-pack

serve:
	$(PY) -m coralcon.cli serve

real:
	CORAL_AVAILABLE=true $(PY) -m coralcon.cli judge-demo --real

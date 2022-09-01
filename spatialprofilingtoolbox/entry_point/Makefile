
build-completions-script: spt-completion.sh

spt-completion.sh:
	@"${MESSAGE}" start "Creating CLI completions script"
	@${PYTHON} -m venv venv
	@source venv/bin/activate ; \
    python -m pip install "../../[control]" ; \
    python build_completions_script.py ; \
    result_code=$$? ; \
    deactivate ; \
    rm -rf venv/ ; \
    rm -rf __pycache__/ ; \
    rm -rf ../../spatialprofilingtoolbox.egg-info/ ; \
    rm -rf ../../build/ ; \
    "${MESSAGE}" end "$$result_code" "Created." "Failed."

clean:
	@rm -f spt-completions.sh
	@rm -rf venv/
	@rm -rf __pycache__/
	@rm -rf ../../spatialprofilingtoolbox.egg-info/
	@rm -rf ../../build/

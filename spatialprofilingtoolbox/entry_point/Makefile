
build-completions-script: spt-completion.sh
	@echo > /dev/null

spt-completion.sh: spt-completion.sh.jinja spt_enable_completion.py build_completions_script.py
	@"${MESSAGE}" start "Creating spt CLI completions script"
	@source ../../venvs/building/bin/activate ; \
    ${PYTHON} build_completions_script.py ; \
    result_code=$$? ; \
    deactivate ; \
    "${MESSAGE}" end "$$result_code" "Created." "Failed."

clean:
	@rm -f spt-completion.sh

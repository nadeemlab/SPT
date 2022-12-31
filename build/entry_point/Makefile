.RECIPEPREFIX = >

spt-completion.sh: ${COMPLETIONS_DIRECTORY}/spt-completion.sh.jinja ${COMPLETIONS_DIRECTORY}/spt_enable_completion.py ${COMPLETIONS_DIRECTORY}/build_completions_script.py venv/touch.txt
>@${MESSAGE} start "Creating spt CLI completions script"
>@source venv/bin/activate ; \
    python -m pip install --no-deps -e ../../ ; \
    python ${COMPLETIONS_DIRECTORY}/build_completions_script.py ; \
    echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Created." "Failed."
>@rm -rf __pycache__
>@rm -f status_code
>@rm -rf ../../${PACKAGE_NAME}.egg-info/

venv/touch.txt:
>@${MESSAGE} start "Creating venv for basic package introspection"
>@rm -rf venv/; \
    python -m venv venv && \
    source venv/bin/activate && \
    python -m pip install jinja2 ; \
    echo "$$?" > status_code ; \
    deactivate ; \
    touch venv/touch.txt
>@${MESSAGE} end "Created." "Failed."
>@rm -f status_code

clean:
>@rm -f spt-completion.sh
>@rm -f status_code
>@rm -rf venv/
>@rm -rf ${PACKAGE_NAME}.egg-info/

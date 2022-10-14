.RECIPEPREFIX = >

build-completions-script: spt-completion.sh
>@echo > /dev/null

# spt-completion.sh: spt-completion.sh.jinja spt_enable_completion.py build_completions_script.py
# >@${MESSAGE} start "Creating spt CLI completions script"
# >@docker run --rm --mount type=bind,src=${COMPLETIONS_DIRECTORY},dst=/mount_sources -t ${DOCKER_ORG_NAME}-package-introspection/${DOCKER_REPO_PREFIX}-package-introspection:latest /bin/bash -c 'cd /mount_sources; PYTHONDONTWRITEBYTECODE=1 python build_completions_script.py' ; \
#     echo "$$?" > status_code
# >@${MESSAGE} end "Created." "Failed."
# >@rm -rf __pycache__
# >@rm -f status_code

spt-completion.sh: spt-completion.sh.jinja spt_enable_completion.py build_completions_script.py create-simple-venv
>@${MESSAGE} start "Creating spt CLI completions script"
>@source venv/bin/activate ; \
    python -m pip install --no-deps ../../ ; \
    python build_completions_script.py ; \
    echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Created." "Failed."
>@rm -rf __pycache__
>@rm -f status_code
>@rm -rf ../../${PACKAGE_NAME}.egg-info/

create-simple-venv: venv/touch.txt

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

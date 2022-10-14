.RECIPEPREFIX = >

build-completions-script: spt-completion.sh
>@echo > /dev/null

spt-completion.sh: spt-completion.sh.jinja spt_enable_completion.py build_completions_script.py
>@${MESSAGE} start "Creating spt CLI completions script"
>@docker run --rm --mount type=bind,src=${COMPLETIONS_DIRECTORY},dst=/mount_sources -t ${DOCKER_ORG_NAME}-package-introspection/${DOCKER_REPO_PREFIX}-package-introspection:latest /bin/bash -c 'cd /mount_sources; PYTHONDONTWRITEBYTECODE=1 python build_completions_script.py' ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Created." "Failed."
>@rm -rf __pycache__
>@rm -f status_code

clean:
>@rm -f spt-completion.sh
>@rm -f status_code

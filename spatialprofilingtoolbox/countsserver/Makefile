
build-dockerfile: Dockerfile

Dockerfile:
	@cat ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base ./Dockerfile.append > Dockerfile

unit-tests:
	@source ../../venvs/building/bin/activate ; \
    for test_script in $$(find unit_tests/test_* | grep "\(\.sh\|\.py\)$$" ) ; \
    do \
        test_name=$${test_script/unit_tests\/test_/} ; \
        extension=$$(echo $$test_name | grep -o "\(\.sh\|\.py\)$$") ; \
        test_name=$${test_name/$$extension/} ; \
        test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
        "${MESSAGE}" start "Testing $$test_name" ; \
        executor=none-cmd ; \
        if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
        if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
        $$executor $$test_script >/dev/null 2>&1 ; \
        "${MESSAGE}" end "$$?" "Passed." "Failed." ; \
    done ; \
    deactivate

module-tests:
	@docker compose up -d >/dev/null 2>&1
	@sleep 2s
	@source ../../venvs/building/bin/activate ; \
    for test_script in $$(find module_tests/test_* | grep "\(\.sh\|\.py\)$$" ) ; \
    do \
        test_name=$${test_script/module_tests\/test_/} ; \
        extension=$$(echo $$test_name | grep -o "\(\.sh\|\.py\)$$" ) ; \
        test_name=$${test_name/$$extension/} ; \
        test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
        "${MESSAGE}" start "Testing $$test_name" ; \
        executor=none-cmd ; \
        if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
        if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
        $$executor $$test_script >/dev/null 2>&1 ; \
        "${MESSAGE}" end "$$?" "Passed." "Failed." ; \
    done ; \
    deactivate
	@docker compose down >/dev/null 2>&1

clean:
	@rm -f Dockerfile
	@rm -f ${WHEEL_FILENAME}

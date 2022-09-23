
build-dockerfile:
	@ echo >/dev/null

unit-tests:
	@docker compose --project-directory ../db/ up -d
	@sleep 2s
	@source ../../venvs/apiserver/bin/activate ; \
    for test_script in $$(find unit_tests/test_* | grep "\(\.sh\|\.py\)$$" ) ; \
    do \
        test_name=$${test_script/unit_tests\/test_/} ; \
        extension=$$(echo $$test_name | grep -o "\(\.sh\|\.py\)$$") ; \
        test_name=$${test_name/$$extension/} ; \
        test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
        ${MESSAGE} start "Testing $$test_name" ; \
        executor=none-cmd ; \
        if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
        if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
        $$executor $$test_script ; echo "$$?" > status_code ; \
        ${MESSAGE} end "Passed." "Failed." ; \
    done ; \
    deactivate
	@docker compose --project-directory ../db/ rm --force --stop ; sleep 1s
	@rm -f status_code

module-tests:
	@docker compose up -d
	@sleep 2s
	@source ../../venvs/workflow/bin/activate ; \
    cd ../workflow && bash module_tests/test_HALO_exported_data_import.sh ; cd ../apiserver/ ; \
    deactivate
	@source ../../venvs/apiserver/bin/activate ; \
    for test_script in $$(find module_tests/test_* | grep "\(\.sh\|\.py\)$$" ) ; \
    do \
        test_name=$${test_script/module_tests\/test_/} ; \
        extension=$$(echo $$test_name | grep -o "\(\.sh\|\.py\)$$" ) ; \
        test_name=$${test_name/$$extension/} ; \
        test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
        ${MESSAGE} start "Testing $$test_name" ; \
        executor=none-cmd ; \
        if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
        if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
        $$executor $$test_script ; echo "$$?" > status_code ; \
        ${MESSAGE} end "Passed." "Failed." ; \
    done ; \
    deactivate
	@docker compose rm --force --stop ; sleep 1s
	@rm -f status_code

clean:
	@rm -f ${WHEEL_FILENAME}
	@rm -f status_code


build-dockerfile: Dockerfile

Dockerfile:
	@cat ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base ./Dockerfile.append > Dockerfile

unit-tests:
	@echo '<unit tests>'

module-tests:
	@echo '<module tests>'

clean:
	@rm -f Dockerfile
	@rm -f ${WHEEL_FILENAME}

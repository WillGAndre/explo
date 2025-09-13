.PHONY: build-c build-a purge controller agent

CDEP := controller/requirements.txt
CENV := controller/cvenv
ADEP := agent/requirements.txt
AENV := agent/avenv

build-c:
	@if [ -d "${CENV}" ]; then rm -rf ${CENV}; fi
	@python3 -m venv ${CENV}
	@. ${CENV}/bin/activate; pip3 install -r ${CDEP}

build-a:
	@if [ -d "${AENV}" ]; then rm -rf ${AENV}; fi
	@python3 -m venv ${AENV}
	@. ${AENV}/bin/activate; pip3 install -r ${ADEP}

purge:
	@rm -rf ${CENV} ${AENV} *.session .env.a

controller:
	@if [ -d "${CENV}" ]; then . ${CENV}/bin/activate; python3 -m $@.$@; fi

agent:
	@if [ -d "${AENV}" ]; then . ${AENV}/bin/activate; python3 -m $@.$@; fi
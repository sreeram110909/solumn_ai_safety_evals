.PHONY: dev stop test

dev:
	@nohup python3 -m report.server > .devserver.log 2>&1 & echo $$! > .devserver.pid; sleep 0.5; echo "dev server on :8085 (pid $$(cat .devserver.pid))"

stop:
	@[ -f .devserver.pid ] && kill $$(cat .devserver.pid) 2>/dev/null; rm -f .devserver.pid; echo "dev server stopped"

test:
	python3 -m pytest -q

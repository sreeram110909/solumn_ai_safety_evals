.PHONY: ci test update-golden

ci: test

test:
	python -m pytest -q

update-golden:
	python -m billing.invoice --regen-golden

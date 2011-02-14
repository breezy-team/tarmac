test-fail:
	trial this-will-fail

release:
	python setup.py sdist
	cd dist
	gpg --armor --sign --detach-sig `find . -name "tarmac-*"`

.PHONY: test test-fail

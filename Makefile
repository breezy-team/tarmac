test-fail:
	trial this-will-fail

build:
	mkdir build
	mkdir build/docs

build/docs/introduction.html: build docs/introduction.txt
	rst2html docs/introduction.txt build/docs/introduction.html

build/docs/writingplugins.html: build docs/writingplugins.txt
	rst2html docs/writingplugins.txt build/docs/writingplugins.html

doc: build/docs/introduction.html build/docs/writingplugins.html

clean:
	rm -rf build

release:
	python setup.py sdist
	cd dist
	gpg --armor --sign --detach-sig `find . -name "tarmac-*"`

.PHONY: test test-fail

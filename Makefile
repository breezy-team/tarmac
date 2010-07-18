TESTFLAGS=
test:
	trial $(TESTFLAGS) tarmac

test-fail:
	trial this-will-fail

build:
	mkdir build
	mkdir build/docs

build/docs/introduction.html: build
	rst2html docs/introduction.txt build/docs/introduction.html

build/docs/writingplugins.html: build
	rst2html docs/writingplugins.txt build/docs/writingplugins.html

doc: build/docs/introduction.html build/docs/writingplugins.html

clean:
	rm -rf build

.PHONY: test test-fail

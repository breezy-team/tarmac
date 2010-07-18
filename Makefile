TESTFLAGS=
test:
	trial $(TESTFLAGS) tarmac

test-fail:
	trial this-will-fail

build:
	mkdir build
	mkdir build/docs

docs/introduction.html: build
	rst2html docs/introduction.txt build/docs/introduction.html

doc: docs/introduction.html

clean:
	rm -rf build

.PHONY: test test-fail

.PHONY: build check test serve
build:
	python3 tools/build-browser-world.py
check: build
	python3 tools/check-browser-content.py
	python3 tools/check-browser-style.py
	python3 tools/check-browser-dependencies.py
test: check
	python3 tools/test-browser-responsiveness.py
	python3 tools/smoke-browser-world.py --full-gameplay
serve: build
	python3 -m http.server 8080 --bind 127.0.0.1 --directory .runtime/browser-world

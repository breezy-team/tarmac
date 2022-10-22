all: container-image

container-image:
	buildah build -t ghcr.io/jelmer/tarmac:latest .
	buildah push ghcr.io/jelmer/tarmac:latest

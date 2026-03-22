.PHONY: mp3 help

ID ?=
EXTRA ?=

help:
	@echo "make mp3 ID=<id_do_video>  [EXTRA='--verbose']"

mp3:
ifeq ($(strip $(ID)),)
	$(error Uso: make mp3 ID=<id_do_video>)
endif
	docker compose run --rm djdanet "https://www.youtube.com/watch?v=$(strip $(ID))" mp3 $(EXTRA)

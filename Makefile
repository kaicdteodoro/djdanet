.PHONY: mp3 pitch help

ID ?=
FILE ?=
SEMITONES ?= -1
EXTRA ?=

help:
	@echo "make mp3 ID=<id_do_video>  [EXTRA='--verbose']"
	@echo "make pitch FILE=<arquivo_em_downloads/> [SEMITONES=-1] [EXTRA='--verbose']"

mp3:
ifeq ($(strip $(ID)),)
	$(error Uso: make mp3 ID=<id_do_video>)
endif
	docker compose run --rm djdanet "https://www.youtube.com/watch?v=$(strip $(ID))" mp3 $(EXTRA)

pitch:
ifeq ($(strip $(FILE)),)
	$(error Uso: make pitch FILE=<arquivo_em_downloads/> [SEMITONES=-1])
endif
	docker compose run --rm djdanet pitch "/app/downloads/$(notdir $(strip $(FILE)))" --semitones $(strip $(SEMITONES)) $(EXTRA)

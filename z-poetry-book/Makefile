PYTHON ?= python3
THEMES ?= song-mist celadon ink-zen cinnabar-seal moon-river bamboo
ARTICLE_FLAGS = --theme celadon --title "打平 DeepInfer" --subtitle "SGLang 与 vLLM 联袂反攻" --author "AI学习的老章" --series "AI技术专题" --edition "大模型推理观察 · 2026年10月" --seal "老章" --require "954K tokens/s" --require "38.96" --require "百川汇海"

.PHONY: install test examples article-examples check clean

install:
	$(PYTHON) scripts/install.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

examples:
	rm -rf dist/poetry
	set -e; for theme in $(THEMES); do \
		$(PYTHON) scripts/render_book.py --input examples/book.json --theme "$$theme" --output "dist/poetry/$$theme"; \
	done

article-examples:
	rm -rf dist/laozhang-deepinfer dist/technical-fixture dist/technical-fixture-assets
	$(PYTHON) scripts/render_article.py --input examples/laozhang-deepinfer/source.md --assets-dir examples/laozhang-deepinfer --offline --output dist/laozhang-deepinfer $(ARTICLE_FLAGS)
	$(PYTHON) scripts/render_article.py --input examples/technical-fixture.md --offline --output dist/technical-fixture --theme ink-zen --require "long_value" --require "Prefill"

check: test examples article-examples

clean:
	rm -rf dist

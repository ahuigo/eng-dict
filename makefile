SHELL := /bin/bash

install:
	@[[ -d ~/bin ]] || mkdir -p ~/bin
	# 1. install trans
	@if ! [[ $$(find ~/bin/trans -type f -size +100k) ]]; then \
		wget git.io/trans -O ~/bin/trans && \
		chmod u+x ~/bin/trans;	\
	fi

	# 2. install translate.py 
	@chmod u+x `pwd`/translate.py 
	ln -sf `pwd`/translate.py ~/bin/t.py
	ln -sf `pwd`/recite.py ~/bin/recite.py

	@# 3. PATH
	@[[ -f ~/words.hash.gz ]] || wget https://github.com/ahuigo/eng-dict/releases/download/v0.1.0/words.hash.gz -O ~/.words.hash.gz
	@[[ "$$PATH" =~ ~/bin ]] || echo $$'请配置：' 'export PATH=$$PATH:~/bin'
	@echo "try: t.py 'hello world'"

	@# 4. install deps
	@pip install -r requirements.txt
clean:
	rm -rf ~/.words.hash{.gz,}
pkg:
	cp ~/.words.hash.gz ./dist/words.hash.gz
	#gh release delete v0.1.0
	gh release create v0.1.0 --notes "mydict" ./dist/*

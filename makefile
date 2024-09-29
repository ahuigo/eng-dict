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

	@# 3. PATH
	@[[ -f ~/.words.hash ]] || wget https://github.com/ahuigo/eng-dict/releases/download/v0.1.0/words.hash -O ~/.words.hash
	@[[ "$$PATH" =~ ~/bin ]] || echo $$'请配置：' 'export PATH=$$PATH:~/bin'
	@echo "try: t.py 'hello world'"

pkg:
	gh release create v0.1.0 --notes "translate in cli" ./dist

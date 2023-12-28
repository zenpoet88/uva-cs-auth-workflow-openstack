
check: requirements.txt *.py Makefile
	python3 -m pyflakes *.py

requirements.txt: *.py Makefile
	pipreqs --force .

clean:




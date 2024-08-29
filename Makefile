
check: *.py Makefile
	python3 -m pyflakes *.py

requirements.txt: *.py Makefile
	pipreqs --force .

clean:
	rm -rf output.json setup-output.json logins.json logins-ouptut.json




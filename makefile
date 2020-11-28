load: ./src/loadInMemory.py 
	python3 ./src/loadInMemory.py
fillTables: ./src/fillTables.py
	python3 ./src/fillTables.py
fillTables-multithreaded: ./src/fillTables.py
	python3 ./src/fillTables.py true
fillIndexer: ./src/fillIndexer.py ./src/loadInMemory.py
	python3 ./src/loadInMemory.py
	python3 ./src/fillIndexer.py
fillAll: ./src/fillTables.py ./src/fillIndexer.py
	python3 ./src/fillTables.py
	python3 ./src/fillIndexer.py
search: ./src/search.py
	python3 ./src/search.py
nuke-ES: 
	curl -X DELETE 'http://localhost:9200/_all'
updateModel: ./src/updateModel.py
	python3 ./src/updateModel.py
installLibraries: 
	pip3 install feedparser
	pip3 install beautifulsoup4
	pip3 install memory-tempfile
	pip3 install elasticsearch
	pip3 install more_itertools
	pip3 install snowballstemmer
	pip3 install more-itertools
	pip3 install stop-words
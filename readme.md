# Fouine

Project for fetching and indexing data into ElasticSearch instance and python shelves

## Installation

Download or clone the project.

In the installed file, just run the installation script (assuming you have a working python3 install)

```bash
make installLibraries
```

## Usage

```bash
make fillAll
```

```bash
make fillTables-multithreaded
```

```bash
make updateModel
```

```bash
make fillIndexer
```

```bash
make search
```

## Used libraries

- feedparser (https://pythonhosted.org/feedparser/)
    - Copyright: https://github.com/kurtmckee/feedparser/blob/develop/LICENSE
- Beautiful Soup (https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
    - Copyright: https://github.com/wention/BeautifulSoup4/blob/master/COPYING.txt
- memory-tempfile (https://github.com/mbello/memory-tempfile)
    - Copyrigtht: https://github.com/mbello/memory-tempfile/blob/master/LICENSE.txt
- ElasticSearch (https://elasticsearch-py.readthedocs.io/en/7.9.1/)
    - Copyright: https://github.com/elastic/elasticsearch-py/blob/master/LICENSE
- more_itertools (https://github.com/more-itertools/more-itertools)
    - Copyright: https://github.com/more-itertools/more-itertools/blob/master/LICENSE

## File structure

```
.
+-- content
|   +-- All fetchers workers data
+-- docs
|   +-- All of the projects classes pydoc, plus the project UML diagram
+-- src
|   +-- All the python code, as well as the list of RSS feed URLs in a txt file
```

## Comparaison de Classificateurs (SP3)
Les résultats de tests peuvent être observé dans le ficher docs/classifiersComparison.txt 
Pour toute les langues et pour tout les algorithmes de classifications testé, les résultats utilisants TfIdf sont de qualité moindre.
Les meilleurs classifier sont la regression logistique, le réseau de neurone et la random forest.

## Basic explainations (FR)

Le programme permet de créer des dossiers contenant les contenus respectif d'un ensemble de flux RSS, il permet de plus de remplir une instance d'Elastic Search avec les données stockées dans ses dossiers. 
Ces dossiers se composent d'un shelf, qui contient, les données collectées, et un fichier texte. Ce fichier texte contient, si l'URL du flux RSS correspondant est valide, la date de dernière modification, le dernier ETag connu, ainsi que l'éventuelle url corrigée du flux RSS.
Le contenu de l'ensemble de ces dossiers peut être fusionné dans un dossier qui sera nommé FetcherDataPool.

MAJ SP2: Le module Indexer est capable de mettre à jour des champs existants, de plus chaque flux RSS ont désormais un label associé.

MAJ SP3: Le module Indexer est capable de classifier les entrées indépendamment, par l'intermédiaire des méthodes du nouveau module Vectoriser.py. Le modèle de classification est une randomForest pouvant ètre sauvegardé sur disque.

## Usage Example

Assuming elastic search is installed in the home directory

```bash
~/elasticsearch-7.9.2/bin/elasticsearch
```

then on another terminal

```bash
make fillTables-multithreaded
make updateModel
make fillIndexer
make search
```
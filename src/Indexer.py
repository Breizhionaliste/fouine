from elasticsearch import Elasticsearch, exceptions as ESexcept
import requests
from hashlib import md5
import shelve
from dbm import error as dbmerr
from memory_tempfile import MemoryTempfile
import Vectoriser
from joblib import load
from collections import Counter

class Indexer:
    """Class used to index the content of a given shelve into ElasticSearch
    Attributes
    ----------
    sourceDataTable : DbfilenameShelf
    elasticSearch : Elasticsearch
    """

    @staticmethod
    def fill(dataTableSrc_='./FetcherDataPool/data.shelve', elasticSearchURL_ = 'localhost', elasticSearchPort_ = 9200):
        """ [STATIC METHOD] The targeted ElasticSearch instance is filled with the content of the targeted shelve during initialisation.
        Each newly indexed element also receives a guessed label
        Parameters
        ----------
        dataTableSrc_ : str, optional
            The location of the target shelve
        elasticSearchURL_ : str, optional
            The url of the target ElasticSearch instance
        elasticSearchPort_ : str, optional
            The TCP port of the target ElasticSearch instance
        """
        res = requests.get("http://" + elasticSearchURL_ + ":" + str(elasticSearchPort_))
        print("response from ElasticSearch server:\n", str(res.content, "utf-8"), "\n\n")

        print("loading model ...")
        try:
            model = load("./content/trainedModel.joblib")
            vecto = load("./content/vectorizer.joblib")
        except:
            print("could not load trained model, please execute \"make updateModel\"")
            exit()

        try:
            sourceDataTable = shelve.open(dataTableSrc_, flag='r')
        except dbmerr:
            print("Origin shelve not found in default or specified directory")
            print("Attempting from default memory folder")
            try:
                memF = MemoryTempfile().gettempdir() + "/".join(dataTableSrc_.rsplit("/", 2)[1:])
                sourceDataTable = shelve.open(memF, flag='r')
            except dbmerr:
                print("Failed.")
                exit()

        elasticSearch = Elasticsearch([{'host': elasticSearchURL_, 'port': elasticSearchPort_}])
        
        print("Indexing Data ...")
        for (pageID,pageValue) in sourceDataTable.items():
            doc = {
                "title": pageValue[3],
                "date": pageValue[2],
                "language": pageValue[5],
                "url": pageValue[1],
                "description": pageValue[4],
                "rssOrigin": pageValue[0],
                "content": pageValue[6],
                "etag": pageValue[7],
                "label": pageValue[8],
                "predicted": model.predict_proba(
                    vecto.transform([
                        Counter(pageValue[6].split(' '))
                    ])
                )
            }
            try:
                elasticSearch.update(index='rssi', id=pageID, body={"doc": doc})
                print("updating " + str(doc["url"]))
            except ESexcept.NotFoundError:
                elasticSearch.index(index='rssi',id=pageID, body=doc)
                print("indexing " + str(doc["url"]))
        
        sourceDataTable.close()
        print("Done.")

    def __init__(self, elasticSearchURL_ = 'localhost', elasticSearchPort_ = 9200):
        """
        Parameters
        ----------
        elasticSearchURL_ : str, optional
            The url of the target ElasticSearch instance
        elasticSearchPort_ : str, optional
            The TCP port of the target ElasticSearch instance
        """
        res = requests.get("http://" + elasticSearchURL_ + ":" + str(elasticSearchPort_))

        self.elasticSearch = Elasticsearch([{'host': elasticSearchURL_, 'port': elasticSearchPort_}])

    def search(self, repeat_ = False, searchByType_ = False):
        """ Launches a search prompt that prints the items that correspond to the given query
        Parameters
        ----------
        repeat_ : bool, optional
            If True, the script will keep prompting the user for a request until termination
        searchByType_ : bool, optional
            If true, the user must specifie the field in which he is searching for an occurence
        """
        try:
            model = load("./content/trainedModel.joblib")
        except:
            print("could not load trained model, please execute \"make updateModel\"")
            exit()

        def query():
            if searchByType_:
                while True:
                    try:
                        query = input("Enter search [type: desiredContent | example: \"title: Trump\"]")
                        [queryType, queryContent] = query.strip().split(': ')
                        break
                    except ValueError:
                        pass
                    except KeyboardInterrupt:
                        self.elasticSearch.close()
                        print("\nElasticSearch Client closed, search app exit successfull")
                        raise SystemExit from KeyboardInterrupt
                queryResponse = self.elasticSearch.search(body={"query":{"match": {queryType: queryContent}}})
            else:
                try:
                    query = input("Enter search: ")
                    queryContent = query.strip()
                except KeyboardInterrupt:
                    self.elasticSearch.close()
                    print("\nElasticSearch Client closed, search app exit successfull")
                    raise SystemExit from KeyboardInterrupt
                queryResponse = self.elasticSearch.search(body={
                    "query": {
                        "multi_match" : {
                            "query":    queryContent,
                            "fields": [ "title", "date", "language", "url", "description", "rssOrigin", "content", "etag", "label"]
                        }
                    }
                })

            if queryResponse.get('hits') is not None and queryResponse['hits'].get('hits') is not None:
                
                result = list(map(lambda elem: {val:elem['_source'][val]  for val in elem['_source'] if val !="content"}, queryResponse['hits']['hits'])) # dégager le contenu de page
                for elem in result:
                    elem["predicted"] = list(zip(model.classes_, elem["predicted"][0]))
                result = [str(elem) for elem in result]
                print("\n".join(result))
            else:
                print({})
        query()
        while repeat_:
            query()
        self.elasticSearch.close()
        
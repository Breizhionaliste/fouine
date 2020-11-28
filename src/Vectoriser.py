from collections import Counter
from typing import Dict, List, Tuple
from stop_words import get_stop_words
from snowballstemmer import EnglishStemmer, FrenchStemmer
from more_itertools import split_at
import numpy as np


from sklearn.feature_extraction import DictVectorizer, text as skTxt
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import recall_score, f1_score

from scipy.sparse import csr_matrix

def simplify(str_: str, lang_: str) -> str:
    """
    Stemmifies and removes stop words from the given string
    Returns
    -------
    str
        the simplyfied string
    """
    if str_ is None:
        return str_

    langOptions = {
        "en": (get_stop_words("en"), EnglishStemmer()),
        "fr": (get_stop_words("fr"), FrenchStemmer())
    }
    try:
        stopWords, stemmer = langOptions.get(lang_)
    except TypeError:
        return str_

    def stemmify(s_: str):
        return stemmer.stemWord(s_)

    def removeStopWords(s_: str):
        return filter(
            lambda word: word not in stopWords,
            map(
                u''.join,
                filter(
                    len,
                    split_at(s_, lambda x : not x.isalpha() and not x.isnumeric(),  keep_separator=False)
                )
            )
        )
    return u' '.join(stemmify(word) for word in removeStopWords(str_.lower()))

def getTfidf(str_: List[str]) -> Tuple[Dict[str, float], DictVectorizer]:
    """
    Processes the tfIdf of the given corpus of strings and returns the relevent objects
    Returns
    -------
    Tuple
        The TfIdf Dictionnary and the corresponding vectoriser
    """
    tfIdfVecto = skTxt.TfidfVectorizer(use_idf=True)
    tfIdfMat = tfIdfVecto.fit_transform(str_)

    tfIdfDict = {k: v.item((0,0)) for (k,v) in zip(tfIdfVecto.get_feature_names(), tfIdfMat.T.todense())}
    return (tfIdfDict, DictVectorizer(sparse=False).fit([tfIdfDict]))

#en appelant cette fonction il faudra mettre un DictVectoriser sur lequel fit() a été appelé
def vectoriseStr(str_: str, tfidfWeights_ : Dict[str, float], translator_: DictVectorizer):
    """
    Returns the weight vector for the given string on the basis of the existing global tfIdf weights

    Returns
    -------
    Array
        the word vector
    """
    cnt: dict = Counter(str_.split(' '))
    weighted = {k: tfidfWeights_[k]*cnt.get(k, 0.0) for k in tfidfWeights_}
    return translator_.transform(weighted)[0]

def vectoriseAsSparse(strList_: List[str], tfidfDict_: Dict[str, float], tfidfVec_):
    """
    returns a sparse tfIdf matrix, meant to be used for generating training and testing data
    """
    return csr_matrix([vectoriseStr(string, tfidfDict_, tfidfVec_) for string in strList_], dtype=np.float)

def vectoriseAsSparse_noTfIdf(strList_: List[str]):
    """
    returns a sparse wordcount matrix that is meant to be used for generating training and testing data
    """
    vectorizer = DictVectorizer(sparse=False)
    vector = vectorizer.fit_transform([Counter(string.split(' ')) for string in strList_])
    return csr_matrix(vector, dtype=float), vectorizer

def train(classifier_: str, xTrain_: List[List[float]], yTrain_: List[str]) -> MultiOutputClassifier:
    """
    Trains and returns a trained model
    Parameters
    ----------
        classifier_: str
            The classifier type, must be one of (\"knn\", \"logreg\", \"nbayes\", \"svm\", \"nn\", \"ranfor\")
        xTrain_: list
            The input traning set
        yTrain: list
            The output/label training set

    Returns
    -------
    MultiOutputClassifier
        The trained model
    """
    classifierOptions : Dict[str, MultiOutputClassifier] = {
        "knn": KNeighborsClassifier(n_neighbors=5),
        "logreg": LogisticRegression(tol=0.1),
        "nbayes": GaussianNB(),
        "svm": SVC(decision_function_shape='ovo'),
        "nn": MLPClassifier(epsilon=1e-1),
        "ranfor": RandomForestClassifier()
    }
    classifier = classifierOptions.get(classifier_)
    classifier.fit(xTrain_, yTrain_)
    return classifier

def printStats(reference_: List[str], predicted_: List[str]):
    """
    Prints the score of the trained model when comparing entries from the test set
    Parameters
    ----------
    reference_: list
        the labels from the test set
    predicted_
        the predicted labels that are to be compared with the existing labels from the test set
    """
    print("accuracy: " + str(1-(sum([ 1 for (a,b) in zip(reference_,predicted_) if a!=b])/len(reference_))))
    print("recall: " + str(recall_score(reference_, predicted_, average="weighted", labels=np.unique(predicted_))))
    print("f-score: " + str(f1_score(reference_, predicted_, average="weighted", labels=np.unique(predicted_))))

import Vectoriser
import Indexer
import shelve
from memory_tempfile import MemoryTempfile
from joblib import dump

sourceDataTable = shelve.open(MemoryTempfile().gettempdir() + '/FetcherDataPool/data.shelve', flag='r')

print("Vectorising data ....")
contents = [
    (v[6],v[8])
    for (_, v) in sourceDataTable.items() if v[5] in ("fr", "en")
]

print("Done.")

print("Classifying data ...")
x, vectorizer = Vectoriser.vectoriseAsSparse_noTfIdf(con[0] for con in contents)
y = [con[1][0] for con in contents]

xTr, xTe, yTr, yTe = Vectoriser.train_test_split(x,y, test_size=0.15)
trainedModel = Vectoriser.train("knn", xTr, yTr)

print("Random Forest results")
trainedModel = Vectoriser.train("ranfor", xTr, yTr)
Vectoriser.printStats(yTe, trainedModel.predict(xTe))

sourceDataTable.close()
print("Done.")

dump(trainedModel, "./content/trainedModel.joblib")
dump(vectorizer, "./content/vectorizer.joblib")

from FetcherPool import FetcherPool
from sys import argv

rssFeedList = [line.rstrip("\n").split(" ") for line in open("./src/feedList.txt").readlines() ]


fPool = FetcherPool(rssFeedList, "./content")
if argv[-1] == "true":
    fPool.launchAll(True)
else:
    fPool.launchAll(False)
fPool.joinAllData()
#fPool.purgeFetcherData()
fPool.save()
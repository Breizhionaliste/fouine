from memory_tempfile import MemoryTempfile
from Indexer import Indexer

Indexer.fill(MemoryTempfile().gettempdir() + '/FetcherDataPool/data.shelve')

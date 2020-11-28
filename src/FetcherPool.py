from Fetcher import Fetcher
import threading
from memory_tempfile import MemoryTempfile
from distutils.dir_util import copy_tree
import os
import shelve
import shutil

class FetcherPool:
    """Class used to fetch and store multiple RSS feeds at once into a single shelve
    Attributes
    ----------
    fetcherList : list
        The list of all Fetcher instances created to handle the given RSS feed URLs
    diskFolder : str
        The folder directory containing the shelve file, located at "." by default
    memoryFolder : str
        Same as diskFolder, except it is located in a directory that is hosted on system RAM
    shelveHandler : DbfilenameShelf
    """

    def __init__(self, rssFeedUrlList_, persistentFld_ = "."):
        """
        Parameters
        ----------
        rssFeedUrlList_ : list
            The list of RSS feeds that the instance must handle, with their associated labels, each element must be [rssURLstrin, label1, label2, ...]
        """

        self.fetcherList = list(map(lambda link: Fetcher(link[0], link[1:], persistentFolder_=persistentFld_), rssFeedUrlList_))

        self.diskFolder = persistentFld_ + '/FetcherDataPool'
        self.memoryFolder = MemoryTempfile().gettempdir() + '/FetcherDataPool'

        try:
            os.mkdir(self.memoryFolder)
        except FileExistsError:
            pass

        try:
            os.mkdir(self.diskFolder)
        except FileExistsError:
            pass

        self.shelveHandler = shelve.open(self.memoryFolder + '/' + "data.shelve")

    def launchAll(self, multithreaded_ = False):
        """ Launches all instances of Fetcher objects in fetcherList
        Parameters
        ----------
        multithreaded_ : bool, optional
            If True, each Fetcher will be launched in parallel, note that prints to console will get chaotic
        """
        if multithreaded_:
            threadList = list(map(lambda fetcher: threading.Thread(target=fetcher.fetchRssFeed, args=(False,)), self.fetcherList))

            for th in threadList:
                th.start()
            for th in threadList:
                th.join()
                
        else:
            for fetcher in self.fetcherList:
                fetcher.fetchRssFeed()
        print("ALL DONE")
        
    def joinAllData(self):
        """Merges all of the instance's Fetcher's shelves into a single shelve
        Returns
        -------
        DbfilenameShelf
            The shelve handler of the single shelve that contains all the merged data
        """
        for fetcher in self.fetcherList:
            fetcher.shelveHandler.close()
            shHandler = shelve.open(fetcher.memoryFolder + "/data.shelve")
            try:
                fLength = os.path.getsize(fetcher.memoryFolder + "/data.shelve")
            except FileNotFoundError:
                try:
                    fLength = os.path.getsize(fetcher.memoryFolder + "/data.shelve.bak")
                except FileNotFoundError:
                    fLength = 0
            if fLength > 0:
                for key in shHandler:
                    try:
                        self.shelveHandler[key] = shHandler[key]
                    except EOFError:
                        del self.shelveHandler[key]
                        print("An element could not be saved for some reason (FetcherPool.py, line 89)")
            shHandler.close()
            
        return self.shelveHandler

    def save(self):
        """
        Saves all data in RAM into persistant folder
        """
        self.shelveHandler.close()
        copy_tree(self.memoryFolder, self.diskFolder)
        for fetcher in self.fetcherList:
            fetcher.save()

    def purgeFetcherData(self):
        """
        Deletes all folders of Fetcher instances (both in RAM and persistent memory), except for the merged folder if it exists
        """
        for fetcher in self.fetcherList:
            shutil.rmtree(fetcher.memoryFolder)
            shutil.rmtree(fetcher.diskFolder)

    def purgeJoinedData(self):
        """
        Deletes the merged folder if it exists ((both in RAM and persistent memory))
        """
        shutil.rmtree(self.memoryFolder)
        shutil.rmtree(self.diskFolder)
        
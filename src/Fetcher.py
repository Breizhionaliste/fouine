#!/usr/bin/python3

import urllib
import urllib.parse as urlParse
from hashlib import md5
import shelve
import feedparser
from bs4 import BeautifulSoup
from langdetect import detect
from memory_tempfile import MemoryTempfile
from distutils.dir_util import copy_tree
import os
from time import gmtime, strftime
import http
import Vectoriser

class Fetcher:
    """Class used to fetch and simplify (read stemmify and remove the stop words) the content pointed by an RSS feed into a python shelve
    Attributes
    ----------
    sourceFeed : str
        The given URL of the RSS feed at initialisation
    id : str
        MD5 hex string Processed from the sourceFeed attribute
    diskFolder : str
        The folder directory containing the shelve file and the correction file, located at "." by default
    memoryFolder : str
        Same as diskFolder, except it is located in a directory that is hosted on system RAM
    shelveHandler : DbfilenameShelf
        The object's shelve handler, opened on the shelve file that is located on memory
    lastModified : str
        The date of either the last time the RSS feed got fetched or the last date given by said RSS feed
    etag : str
        The last ETag given by the RSS feed when it was last fetched
    correctedURL : str
        The server's corrected URL response (HTTP 300 type of response) if the one given at initialisation is temporary
    labels: list
        The list of associated labels (useful for learning algorithms)
    """

    def __init__(self, feedURL_, labels_, persistentFolder_ = "."):
        """
        Parameters
        ----------
        feedURL_ : str
            The url of the RSS feed
        persistentFolder_: str, optional
            Location of the folder in which the content of the fetched feed should be save, default is "."
        """

        self.sourceFeed = feedURL_
        self.labels = labels_
        self.id = str(md5(feedURL_.encode()).hexdigest())
        
        self.diskFolder = persistentFolder_ + '/' + self.id
        self.memoryFolder = MemoryTempfile().gettempdir() + '/' + self.id

        try:
            os.mkdir(self.memoryFolder)
        except FileExistsError:
            pass

        try:
            os.mkdir(self.diskFolder)
        except FileExistsError:
            self.load()

        self.shelveHandler = shelve.open(self.memoryFolder + '/' + "data.shelve")

        self.lastModified = None
        self.etag = None
        self.correctedURL = None

        try:
            fHandle = open(self.memoryFolder + '/' + "lastID", "r")
            fLines = fHandle.readlines()
            fHandle.close()
            fLines = [s.rstrip('\n') for s in fLines]

            if fLines[0] != "400":
                if fLines[0] != "None":
                    self.lastModified = str(fLines[0])
                if fLines[1] != "None":
                    self.etag = str(fLines[1])
                if fLines[2] != "None":
                    self.correctedURL = str(fLines[2])

        except FileNotFoundError:
            fHandle = open(self.memoryFolder + '/' + "lastID", "w+")
            fHandle.write("None\nNone\nNone")
            fHandle.close()

        print("values read in info file for Fetcher " + self.id + " :")
        print("\tcorrected url: " + str(self.correctedURL) + " " + str(type(self.correctedURL)))
        print("\tcorrected last modified: " + str(self.lastModified) + " " + str(type(self.correctedURL)))
        print("\tcorrected etag: " + str(self.etag) + " " + str(type(self.correctedURL)) + "\n")
        
    def save(self):
        """
        Saves the folder's content into persistent memory
        """
        self.shelveHandler.close()
        copy_tree(self.memoryFolder, self.diskFolder)

    def load(self):
        """
        Copies the persistent memory's content into RAM folders
        """
        copy_tree(self.diskFolder, self.memoryFolder)

    def getPageContent(self, url_):
        """ returns the given URL's associated content in string form, if it already exists in the shelve, updates the associated shelve
        Parameters
        ----------
        url_ : str
            The URL of the page to be dowloaded

        Returns
        -------
        str
        """
        def tagVisible(element_):
            if element_.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            return True

        def textFromHtml(body_):
            soup = BeautifulSoup(body_, 'html.parser')
            texts = soup.findAll(text=True)
            visibleTexts = filter(tagVisible, texts)
            return u" ".join(t.strip() for t in visibleTexts)

        url = list(urlParse.urlsplit(url_))
        url[2] = urlParse.quote(url[2])
        url = urlParse.urlunsplit(url)
        

        result = ""
        itemID = md5(url.encode()).hexdigest()
        if itemID in self.shelveHandler:
            print("updating " + url)
            self.updateItem(md5(url.encode()).hexdigest())
            result = self.shelveHandler[itemID][6]
        else:
            print("dowloading " + url)
            try:
                tempFile = urllib.request.urlopen(url)
                result = tempFile.read()
            except (urllib.error.HTTPError, urllib.error.URLError, http.client.RemoteDisconnected):
                return None
            except http.client.InvalidURL:
                try:
                    tempFile = urllib.request.urlopen(url_.replace(' ', "%20"))
                    result = tempFile.read()
                except:
                    return None
            result = textFromHtml(result)
        return result
    
    def updateItem(self, itemID_):
        """Updates the content associated with the given id in the object's shelve if it exists. May or may not redownload the content of the target webpage
        The content of the downloaded page is also stemmified and the detected stop words are removed
        Parameters
        ----------
        itemID_: str
            The ID of the element in the current instance's shelve
        """
        itemData = self.shelveHandler[itemID_]
        date = itemData[2]
        etag = itemData[6]
        
        if date is not None:
            request = urllib.request.Request(url=str(itemData[1]).encode('utf-8'), headers={'If-Modified-Since': date, 'etag': etag})
        else:
            request = str(itemData[1])

        try: 
            urlHandle = urllib.request.urlopen(request)
            sourcePageContent = urlHandle.read()
            date = urlHandle.info().get("Last-Modified")
            etag = urlHandle.info().get("ETag")
            self.shelveHandler[itemID_] = (*itemData[:6], Vectoriser.simplify(u" ".join(item for item in (itemData[3], itemData[4], itemData[6]) if item), itemData[5]), etag, self.labels, None)
        except (urllib.error.HTTPError, urllib.error.URLError):
            pass

    def translateToItemObject(self, rssPost_):
        """ Returns an object that contains the URL's associated content on top of surrounding data
        The content of the downloaded page is also stemmified and the detected stop words are removed
        Parameters
        ----------
        rssPost_ : str
            The URL of the content that must be fetched
        Returns
        -------
        tuple
            A tuple of length 11, containing (in order):
                the ID of the object, the URL of the RSS feed the object was fetched from, the URL of the actual page, the last-modified date, the title of the page, the description of the page, the detected language used, the actual content of the page, the ETAG, the known label of the page (news, blog, ...), the predicted label set to None
        """

        def isToBeTerminated(*candidates_):
            for cdt in candidates_:
                if cdt is None:
                    return True
            return False

        def tryFindNotNone(*candidates_):
            for cdt in candidates_:
                if cdt is not None:
                    return cdt
            return None

        # critical
        webPageOrigin = tryFindNotNone(
            rssPost_.get('link'),
            rssPost_.get('links')[0].href
        )
        if isToBeTerminated(webPageOrigin):
            return None
        identificator = md5(webPageOrigin.encode()).hexdigest()

        # non-critical
        date = tryFindNotNone(
            rssPost_.get('date'),
            rssPost_.get('created'),
            rssPost_.get('updated'),
            strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())
        )
        sourcePageContent = self.getPageContent(webPageOrigin)

        if self.correctedURL is None:
            sourceFeedURL = self.sourceFeed
        else:
            sourceFeedURL = self.correctedURL

        title = rssPost_.get('title')
        description = tryFindNotNone(
            rssPost_.get('summary'),
            rssPost_.get('title_detail').value
        )
        try:
            language = detect(tryFindNotNone(description, title))
        except:
            language = None

        etag = rssPost_.get('etag')
        return (identificator, sourceFeedURL, webPageOrigin, date, title, description, language, Vectoriser.simplify(u" ".join(item for item in (title, description, sourcePageContent) if item), language), etag, self.labels, None)

    def fetchRssFeed(self, closeShelveOnCompletion_=True):
        """ Creates or opens the shelve associated with the targeted RSS feed, and completes it with new or updated web pages given by said feed
        Parameters
        ----------
        closeShelveOnCompletion_: bool, optional
            If false, the shelve is not closed after completion
        Returns
        -------
        tuple
            The location of the memory folder, the location of the persistent folder and the corrected URL if the server associated with the RSS feed sent one
        """
        print("\n")
        print(self.sourceFeed)
        try:
            if self.correctedURL is None:
                d = feedparser.parse(self.sourceFeed, modified=self.lastModified, etag=self.etag)
            else:
                d = feedparser.parse(self.correctedURL, modified=self.lastModified, etag=self.etag)
        except urllib.error.URLError:
            print("The URL is invalid, giving up ...")
            fh = open(self.memoryFolder + '/' + "lastID", "w+")
            fh.write("400")
            fh.close()
            return (self.memoryFolder, self.diskFolder, self.correctedURL)

        print("corrected url: " + str(self.correctedURL))
        print("RSS feed last-modified: " + str(d.get("modified")))
        print("RSS feed etag: " + str(d.get("etag")))

        print("response code from feed: ", d.get("status"))

        if d.get("status") is not None and d.get("status") >= 400:
            fh = open(self.memoryFolder + '/' + "lastID", "w+")
            fh.write("400")
            fh.close()
            self.shelveHandler.close()
        else:
            if d.get("status") is not None and (d.get("status") == 301 or d.get("status") == 308):
                print("RSS feed redirected to ", d.get("href"))
                self.correctedURL = d.get("href")

            for post in d.entries:  # TODO restriction à enlever
                test = self.translateToItemObject(post)
                if test is not None:
                    self.shelveHandler[test[0]] = test[1:]

            if closeShelveOnCompletion_:
                self.shelveHandler.close()

            fh = open(self.memoryFolder + '/' + "lastID", "w+")

            self.lastModified = d.get("modified")
            self.etag = d.get("etag")
            fh.write(str(self.lastModified) + "\n" + str(self.etag) + "\n" + str(self.correctedURL))

            fh.close()

        return (self.memoryFolder, self.diskFolder, self.correctedURL)


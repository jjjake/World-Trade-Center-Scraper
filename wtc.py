#!/usr/bin/python

"""
20111012

wtc.py downloads all of the video available at http://wtcdata.nist.gov.
It creates a directory for each video and downloads the video into this
directory. It also generates an {item}_meta.xml from the metadata found
on wtcdata.nist.gov, and a stub {item}_files.xml. The {item}_files.xml
is created solely for the needs of uploading to archive.org via the 
internal uploading tool, auto_submit.

Requirements:
    o lxml (lxml.html, and etree)

todo:
    o Add support for downloading still images.
    o Better handling of HTTP Errors

"""

import urllib2
from urllib2 import HTTPError
import time
from subprocess import call
import lxml.html
import os
from lxml import etree

def openUrl(url):
    ### Create urllib2 opener, with cookies in the header.
    req = urllib2.Request(url)
    req.add_header('Cookie', '***YOUR COOKIES HERE***')
    html = urllib2.urlopen(req)
    return html

def checkArchive(identifier):
    ### Check archive.org to see if an item exists or not.
    check_item = ('/usr/bin/curl -s --location http://www.archive.org/'
                  'services/check_identifier.php?identifier=' + identifier +
                  '| if grep -q "not_available"; then return 1; fi')
    check_item = str(check_item)
    retcode = call(check_item, shell=True)
    if retcode != 0:
        return 1
    else:
        return 0

def urlList(url, pageType):
    ### Return a list URL's for either a collection page or video page.
    html = openUrl(url).read()
    links = lxml.html.iterlinks(html)
    linkList = []
    for element, attribute, link, pos in links:
        if pageType == 1:
            if link.startswith('/gallery2/v/Collected+Materials/Organized+'
                               'Photos+and+Video+Clips/VideoClips/'):
                if link.endswith('/'):
                    if link.endswith('VideoClips/'):
                        pass
                    else:
                        linkList.append('http://wtcdata.nist.gov%s' % link)
        if pageType == 2:
            if link.endswith('.avi.html'):
                linkList.append('http://wtcdata.nist.gov%s' % link)
    return linkList

def getLastPage(url):
    html = lxml.html.fromstring(openUrl(url).read())
    for element in html.iter():
        if element.tag == 'a':
            try:
                if element.attrib['class'] == 'last':
                    lastPage = 'http://wtcdata.nist.gov%s' % element.attrib['href']
                    lastPage = lastPage.split('=')[-1]
                    return lastPage
            except KeyError:
                pass

def download(mediaUrl, identifier):
    ### Create file downloader.
    retries = 0
    response = openUrl(mediaUrl)
    data = response.read()
    localName = '%s.avi' % identifier
    f = open(localName, 'wb')
    f.write(data)
    f.close()

def main():
    """
    Create './NIST_WTC_Repository' directory if it doesn't exist, and cd
    into it
    """
    if not os.path.exists('NIST_WTC_Repository'):
        os.mkdir('NIST_WTC_Repository')
    os.chdir('NIST_WTC_Repository')
    home = os.getcwd()
    ### Iterate through each collection:
    for i in range(1,14):
        print '\n======\nPage: %s of 14\n ' % i
        url = ('http://wtcdata.nist.gov/gallery2/v/Collected+Materials/'
               'Organized+Photos+and+Video+Clips/VideoClips/?g2_page=%s' % i)
        for collectionPage in urlList(url,1):
            print "\n\n\n\nCollection: -%s-\n\n" % collectionPage
            firstPage = "%s?g2_page=1" % (collectionPage)
            try:
                lastPage = getLastPage(firstPage)
                lastPage = int(lastPage) + 1
            except TypeError:
                lastPage = 1
            for i in range(1,lastPage):
                print '\n\tPage: %s of %s\n' % (i, lastPage)
                collectionPageUrl = "%s?g2_page=%s" % (collectionPage,i)
                ### Iterate through each video item:
                collectionURLs = urlList(collectionPageUrl,2)
                for item in collectionURLs:
                    metaDict = {}
                    os.chdir(home)
                    itemHTML = lxml.html.fromstring(openUrl(item).read())
                    ### Get link to video:
                    links = lxml.html.iterlinks(itemHTML)
                    for element, attribute, link, pos in links:
                        if link.endswith('.avi'):
                            mediaUrl = 'http://wtcdata.nist.gov%s' % link
                    ### Parse metadata into {item}_meta.xml:
                    for element in itemHTML.iter():
                        if element.tag == 'h2':
                            title = str(element.text)
                            title = title.replace('.avi', '')
                            title = title.lstrip()
                            title = title.rstrip()
                            metaDict['title'] = title
                            identifier = title.replace(' ', '')
                            identifier = identifier.replace('&', 'and')
                        if element.tag == 'p':
                            try:
                                if element.attrib['class'] == 'giDescription':
                                    description = element.text_content()
                                    metaDict['description'] = description
                            except KeyError:
                                pass
                        if element.tag == 'div':
                            try:
                                if element.attrib['class'] == 'block-tags-ImageTags':
                                    subject = element.text_content()
                                    subject = subject.replace('\n', '')
                                    subject = subject.replace('Tags: ', '')
                                    subject = subject.split(',')
                                    subject = ';'.join(subject)
                                    metaDict['subject'] = subject
                            except KeyError:
                                pass
                        if element.tag == 'meta':
                            attribDict = element.attrib
                            if attribDict.get('name') == 'DC.creator':
                                metaDict['creator'] = attribDict['content']
                            if attribDict.get('name') == 'DC.date.created':
                                metaDict['date'] = attribDict['content']
                            if attribDict.get('name') == 'DC.date.reviewed':
                                metaDict['date_reviewed'] = attribDict['content']
                    """
                    If the item doesn't exist create the metadata files and
                    download the video:
                    """
                    if checkArchive(identifier) == 0:
                        if not os.path.exists(identifier):
                            os.mkdir(identifier)
                        os.chdir(identifier)
                        print '\n\tCreating item: %s\n' % identifier
                        print '\t\to Generating %s_meta.xml\n' % identifier
                        root = etree.Element("metadata")
                        for k,v in metaDict.iteritems():
                            subElement = etree.SubElement(root, k)
                            subElement.text = v
                        collection = etree.SubElement(root, 'collection')
                        collection.text = 'NIST_WTC_Repository'
                        mediatype = etree.SubElement(root, 'mediatype')
                        mediatype.text = 'movies'
                        metaXml = etree.tostring(root, pretty_print=True,
                                                 xml_declaration=True, encoding="utf-8")
                        f = open('%s_files.xml' % identifier, 'wb')
                        f.write('<files/>')
                        f.close()
                        fm = open('%s_meta.xml' % identifier, 'wb')
                        fm.write(metaXml)
                        fm.close()
                        print '\t\to Downloading %s from: %s\n' % (identifier, mediaUrl)
                        download(mediaUrl, identifier)
                    """
                    And if the item already exists, skip it and move on to the
                    next item.
                    """
                    if checkArchive(identifier) == 1:
                        print '\n\t*** %s is already on the Archive ***\n' % identifier
                        pass

if __name__ == '__main__':
    main()


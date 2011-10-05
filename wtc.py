#!/usr/bin/python

import urllib2
from urllib2 import HTTPError
import time
from subprocess import call
import lxml.html
import os
from lxml import etree

def openUrl(url):
    req = urllib2.Request(url)
    req.add_header('Cookie', 'fsr.s={\"v\":1,\"rid\":\"1317666021582_6219\",'
                   '\"pv\":12,\"to\":5,\"c\":\"http://www.nist.gov/manuscript'
                   '-publication-search.cfm\",\"lc\":{\"d0\":{\"v\":12,\"s\":'
                   'true}},\"cd\":0,\"sd\":0,\"f\":1317671614982,\"l\":\"en\"'
                   ',\"i\":-1}; MessageAccepted=1; route=0')
    html = urllib2.urlopen(req)
    return html

def checkArchive(identifier):
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

def download(mediaUrl, identifier):
    retries = 0
    response = openUrl(mediaUrl)
    data = response.read()
    localName = '%s.avi' % identifier
    f = open(localName, 'wb')
    f.write(data)
    f.close()

def main():
    if not os.path.exists('NIST_WTC_Repository'):
        os.mkdir('NIST_WTC_Repository')
    os.chdir('NIST_WTC_Repository')
    home = os.getcwd()
    for i in range(1,14):
        print '\n======\nPage: %s\n' % i
        ### Collection page iteration:
        url = ('http://wtcdata.nist.gov/gallery2/v/Collected+Materials/'
               'Organized+Photos+and+Video+Clips/VideoClips/?g2_page=%s' % i)
        for collection in urlList(url,1):
            ### Item page iteration:
            for item in urlList(collection,2):
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
                        if not os.path.exists(identifier):
                            os.mkdir(identifier)
                        os.chdir(identifier)
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
                if checkArchive(identifier) == 0:
                    print '\n---\nCreating item: %s\n' % identifier
                    print '    o Generating %s_meta.xml\n' % identifier
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
                    print '    o Downloading %s from: %s\n' % (identifier, mediaUrl)
                    download(mediaUrl, identifier)
                if checkArchive(identifier) == 1:
                    print '\n*** %s is already on the Archive ***\n' % identifier
                    pass

if __name__ == '__main__':
    main()


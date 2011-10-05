#!/opt/local/bin/python

import urllib2
import lxml.html
import re

def openUrl(url):
    req = urllib2.Request(url)
    req.add_header('Cookie', 'fsr.s={\"v\":1,\"rid\":\"1317666021582_6219\",'
                   '\"pv\":12,\"to\":5,\"c\":\"http://www.nist.gov/manuscript'
                   '-publication-search.cfm\",\"lc\":{\"d0\":{\"v\":12,\"s\":'
                   'true}},\"cd\":0,\"sd\":0,\"f\":1317671614982,\"l\":\"en\"'
                   ',\"i\":-1}; MessageAccepted=1; route=0')
    html = urllib2.urlopen(req)
    return html

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

def main():
    for i in range(1,14):
        ### Collection page iteration:
        url = ('http://wtcdata.nist.gov/gallery2/v/Collected+Materials/'
               'Organized+Photos+and+Video+Clips/VideoClips/?g2_page=%s' % i)
        for collection in urlList(url,1):
            ### Item page iteration:
            for item in urlList(collection,2):
                itemHTML = lxml.html.fromstring(openUrl(item).read())
                for element in itemHTML.iter():
                    if element.tag == 'meta':
                        print element.attrib


if __name__ == '__main__':
    main()


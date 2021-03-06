# -*- coding: utf-8 -*-
# -- coding: utf-8 --
# Copyright 2013 Fanficdownloader team, 2017 FanFicFare team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
####################################################################################################
###   Adapted by GComyn - November 26, 2016
###
####################################################################################################
from __future__ import unicode_literals
import time
import logging
logger = logging.getLogger(__name__)
import re
import sys
import urllib2
from bs4 import UnicodeDammit, Comment

from ..htmlcleanup import stripHTML
from .. import exceptions as exceptions

from base_adapter import BaseSiteAdapter,  makeDate

####################################################################################################
def getClass():
    return FanficAuthorsNetAdapter

# Class name has to be unique.  Our convention is camel case the
# sitename with Adapter at the end.  www is skipped.
class FanficAuthorsNetAdapter(BaseSiteAdapter):

    def __init__(self, config, url):
        BaseSiteAdapter.__init__(self, config, url)
        logger.debug("FanficAuthorsNetAdapter.__init__ - url='{0}'".format(url))

        self.username = "NoneGiven" # if left empty, site doesn't return any message at all.
        self.password = ""
        self.is_adult=False

        # get storyId from url
        self.story.setMetadata('storyId',self.parsedUrl.path.split('/',)[1])

        #Setting the 'Zone' for each "Site"
        self.zone = self.parsedUrl.netloc.replace('.fanficauthors.net','')

        # normalized story URL.
        self._setURL('http://{0}.{1}/{2}/'.format(
            self.zone, self.getBaseDomain(), self.story.getMetadata('storyId')))

        # Each adapter needs to have a unique site abbreviation.
        self.story.setMetadata('siteabbrev','ffa')

        # The date format will vary from site to site.
        # http://docs.python.org/library/datetime.html#strftime-strptime-behavior
        self.dateformat = "%d %b %y"
        
    ################################################################################################
    def getBaseDomain(self):
        ''' Added because fanficauthors.net does send you to www.fanficauthors.net when 
            you go to it '''
        return 'fanficauthors.net'

    ################################################################################################
    @staticmethod # must be @staticmethod, don't remove it.
    def getSiteDomain():
        return 'www.fanficauthors.net'

    ################################################################################################
    @classmethod
    def getAcceptDomains(cls):

        return ['aaran-st-vines.nsns.fanficauthors.net',
                'abraxan.fanficauthors.net',
                'bobmin.fanficauthors.net',
                'canoncansodoff.fanficauthors.net',
                'chemprof.fanficauthors.net',
                'copperbadge.fanficauthors.net',
                'crys.fanficauthors.net',
                'deluded-musings.fanficauthors.net',
                'draco664.fanficauthors.net',
                'fp.fanficauthors.net',
                'frenchsession.fanficauthors.net',
                'ishtar.fanficauthors.net',
                'jbern.fanficauthors.net',
                'jeconais.fanficauthors.net',
                'kinsfire.fanficauthors.net',
                'kokopelli.nsns.fanficauthors.net',
                'ladya.nsns.fanficauthors.net',
                'lorddwar.fanficauthors.net',
                'mrintel.nsns.fanficauthors.net',
                'musings-of-apathy.fanficauthors.net',
                'ruskbyte.fanficauthors.net',
                'seelvor.fanficauthors.net',
                'tenhawk.fanficauthors.net',
                'viridian.fanficauthors.net',
                'whydoyouneedtoknow.fanficauthors.net']

    ################################################################################################
    @classmethod
    def getSiteExampleURLs(self):
        return ("http://aaran-st-vines.nsns.fanficauthors.net/[StoryId]/\n"
              + "http://abraxan.fanficauthors.net/[StoryId]/\n"
              + "http://bobmin.fanficauthors.net/[StoryId]/\n"
              + "http://canoncansodoff.fanficauthors.net/[StoryId]/\n"
              + "http://chemprof.fanficauthors.net/[StoryId]/\n"
              + "http://copperbadge.fanficauthors.net/[StoryId]/\n"
              + "http://crys.fanficauthors.net/[StoryId]/\n"
              + "http://deluded-musings.fanficauthors.net/[StoryId]/\n"
              + "http://draco664.fanficauthors.net/[StoryId]/\n"
              + "http://fp.fanficauthors.net/[StoryId]/\n"
              + "http://frenchsession.fanficauthors.net/[StoryId]/\n"
              + "http://ishtar.fanficauthors.net/[StoryId]/\n"
              + "http://jbern.fanficauthors.net/[StoryId]/\n"
              + "http://jeconais.fanficauthors.net/[StoryId]/\n"
              + "http://kinsfire.fanficauthors.net/[StoryId]/\n"
              + "http://kokopelli.nsns.fanficauthors.net/[StoryId]/\n"
              + "http://ladya.nsns.fanficauthors.net/[StoryId]/\n"
              + "http://lorddwar.fanficauthors.net/[StoryId]/\n"
              + "http://mrintel.nsns.fanficauthors.net/[StoryId]/\n"
              + "http://musings-of-apathy.fanficauthors.net/[StoryId]/\n"
              + "http://ruskbyte.fanficauthors.net/[StoryId]/\n"
              + "http://seelvor.fanficauthors.net/[StoryId]/\n"
              + "http://tenhawk.fanficauthors.net/[StoryId]/\n"
              + "http://viridian.fanficauthors.net/[StoryId]/\n"
              + "http://whydoyouneedtoknow.fanficauthors.net/[StoryId]/\n")

    ################################################################################################
    def getSiteURLPattern(self):
        return r'http?://(aaran-st-vines.nsns|abraxan|bobmin|canoncansodoff|chemprof|copperbadge|crys|deluded-musings|draco664|fp|frenchsession|ishtar|jbern|jeconais|kinsfire|kokopelli.nsns|ladya.nsns|lorddwar|mrintel.nsns|musings-of-apathy|ruskbyte|seelvor|tenhawk|viridian|whydoyouneedtoknow)\.fanficauthors\.net/([a-zA-Z0-9_]+)/'

    ################################################################################################
    def doExtractChapterUrlsAndMetadata(self, get_cover=True):

        url = self.url
        logger.debug("URL: "+url)

        params={}
        if self.password:
            params['username'] = self.username
            params['password'] = self.password
        else:
            params['username'] = self.getConfig("username")
            params['password'] = self.getConfig("password")
        
        if not params['username']:
            raise exceptions.FailedToLogin('You need to have your username and pasword set.',params['username'])

        try:
            data = self._fetchUrl(url+'index/', params, usecache=False)
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise exceptions.StoryDoesNotExist("Code: 404. {0}".format(url))
            elif e.code == 410:
                raise exceptions.StoryDoesNotExist("Code: 410. {0}".format(url))
            elif e.code == 401:
                self.needToLogin = True
                data = ''
            else:
                raise e

        if "The requested file has not been found" in data:
            raise exceptions.StoryDoesNotExist(
                "{0}.{1} says: The requested file has not been found".format(
                    self.zone, self.getBaseDomain()))
            
        # use BeautifulSoup HTML parser to make everything easier to find.
        soup = self.make_soup(data)

        # Find authorid and URL. 
        # There is no place where the author's name is listed, 
        # except for in the image at the top of the page. We have to
        # work with the url entered to get the Author's Name
        a = self.zone.split('.')[0]
        self.story.setMetadata('authorId',a)
        a = a.replace('-',' ').title()
        self.story.setMetadata('author',a)
        self.story.setMetadata('authorUrl','http://{0}/'.format(self.parsedUrl.netloc))
        
        loginUrl = self.story.getMetadata('authorUrl')+'account/'
        loginsoup = self.make_soup(self._fetchUrl(loginUrl))
        if True:
#        if self.performLogin(loginUrl, loginsoup):
            # Now go hunting for all the meta data and the chapter list.

            ## Title
            a = soup.find('h2')
            self.story.setMetadata('title',stripHTML(a))

            # Find the chapters:
            # The published and update dates are with the chapter links...
            # so we have to get them from there.
            chapters = soup.findAll('a', href=re.compile('/'+self.story.getMetadata(
                'storyId')+'/([a-zA-Z0-9_]+)/'))

            # Here we are getting the published date. It is the date the first chapter was "updated"
            updatedate = stripHTML(unicode(chapters[0].parent)).split('Uploaded on:')[1].strip()
            updatedate = updatedate.replace('st ',' ').replace('nd ',' ').replace(
                'rd ',' ').replace('th ',' ')
            self.story.setMetadata('datePublished', makeDate(updatedate, self.dateformat))

            for i, chapter in enumerate(chapters):
                if '/reviews/' not in chapter['href']:
                    # here we get the update date. We will update this for every chapter, 
                    # so we get the last one.
                    updatedate = stripHTML(unicode(chapters[i].parent)).split(
                        'Uploaded on:')[1].strip()
                    updatedate = updatedate.replace('st ',' ').replace('nd ',' ').replace(
                        'rd ',' ').replace('th ',' ')
                    self.story.setMetadata('dateUpdated', makeDate(updatedate, self.dateformat))
                    
                    if '::' in stripHTML(unicode(chapter)):
                        chapter_title = stripHTML(unicode(chapter).split('::')[1])
                    else:
                        chapter_title = stripHTML(unicode(chapter))
                    chapter_Url = self.story.getMetadata('authorUrl')+chapter['href'][1:]
                    self.chapterUrls.append((chapter_title, chapter_Url))
            
            self.story.setMetadata('numChapters', len(self.chapterUrls))
            genres = ("Drama","Romance")
            gotgenre = False
            ## Getting the Metadata that is there
            div = soup.find('div',{'class':'well'})
            metads = div.findAll('p')[1].get_text().replace('\n','').split(' - ')
            for metad in metads:
                metad = metad.strip()
                if ':' in metad:
                    heading = metad.split(':')[0].strip()
                    text = metad.split(':')[1].strip()
                    if heading == 'Status':
                        self.story.setMetadata('status',text)
                    elif heading == 'Rating':
                        self.story.setMetadata('rating',text)
                    elif heading == 'Word count':
                        self.story.setMetadata('numWords',text)
                    elif heading == 'Genre':
                        self.story.setMetadata('genre',text.replace(',',', ').replace('  ',' '))
                        gotgenre = True
                else:
                    if gotgenre == True:
                        if ',' in metad:
                            for gen in metad.split(','):
                                self.story.addToList('genre',gen.strip())
                                for gen in genres:
                                    if metad == gen:
                                        self.story.addToList('genre',metad.strip())
                        else:
                            for gen in genres:
                                if metad == gen:
                                    self.story.addToList('genre',metad.strip())
                    

            summary = div.find('blockquote').get_text()
            self.setDescription(url,summary)
                        
    # grab the text for an individual chapter.
    def getChapterText(self, url):
        logger.debug('Getting chapter text from: %s' % url)

        soup = self.make_soup(self._fetchUrl(url))

        story = soup.find('div',{'class':'story'})
        
        if story == None:
            raise exceptions.FailedToDownload(
                "Error downloading Chapter: '{0}'!  Missing required element!".format(url))

        #Now, there are a lot of extranious tags within the story division.. so we will remove them.
        for tag in story.findAll('ul',{'class':'pager'}) + story.findAll(
            'div',{'class':'alert'}) + story.findAll('div', {'class':'btn-group'}):
            tag.extract()
        
        return self.utf8FromSoup(url,story)

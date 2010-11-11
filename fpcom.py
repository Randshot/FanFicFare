# -*- coding: utf-8 -*-

import os
import re
import sys
import cgi
import uuid
import shutil
import os.path
import logging
import unittest
import urllib as u
import pprint as pp
import urllib2 as u2
import urlparse as up
import BeautifulSoup as bs
import htmlentitydefs as hdefs
import time
import datetime

from constants import *
from adapter import *

try:
	import login_password
except:
	# tough luck
	pass

try:
	from google.appengine.api.urlfetch import fetch as googlefetch
	appEngine = True
except:
	appEngine = False

class FPCom(FanfictionSiteAdapter):
	def __init__(self, url):
		self.url = url
		parsedUrl = up.urlparse(url)
		self.host = parsedUrl.netloc
		self.path = parsedUrl.path
		
		self.storyName = 'Story'
		self.authorName = 'Author'
		self.outputName = 'Story'
		self.storyDescription = 'A Story'
		self.storyCharacters = []
		self.storySeries = ''
		self.authorId = '0'
		self.authorURL = self.path
		self.storyId = '0'
		self.storyPublished = datetime.date(1970, 01, 31)
		self.storyCreated = datetime.datetime.now()
		self.storyUpdated = datetime.date(1970, 01, 31)
		self.languageId = 'en-UK'
		self.language = 'English'
		self.subjects = []
		logging.debug('self.subjects=%s' % self.subjects)
		self.publisher = self.host
		self.numChapters = 0
		self.numWords = 0
		self.genre = 'Fiction'
		self.category = 'Category'
		self.storyStatus = 'In-Progress'
		self.storyRating = 'K'
		self.storyUserRating = '0'
		
		logging.debug('self.path=%s' % self.path)

		if self.path.startswith('/'):
			self.path = self.path[1:]
		
		spl = self.path.split('/')
		logging.debug('spl=%s' % spl)
		if spl is not None:
			if len(spl) > 0 and spl[0] != 's':
				logging.error("Error URL \"%s\" is not a story." % self.url)
				exit (20)				
			if len(spl) > 1:
				self.storyId = spl[1]
			if len(spl) > 2:
				chapter = spl[1]
			else:
				chapter = '1'
			if len(spl) == 5:
				self.path = "/".join(spl[1:-1])
				self.outputName = spl[4] + '-ffnet_' + spl[2]
		
		if self.path.endswith('/'):
			self.path = self.path[:-1]
		
		logging.debug('self.path=%s' % self.path)
		
		self.uuid = 'urn:uuid:' + self.host + '-u.' + self.authorId + '-s.' + self.storyId
		logging.debug('self.uuid=%s' % self.uuid)

		logging.debug('self.storyId=%s, chapter=%s, self.outputName=%s' % (self.storyId, chapter, self.outputName))
		if not appEngine:
			self.opener = u2.build_opener(u2.HTTPCookieProcessor())
		else:
			self.opener = None
	
		logging.debug("Created FF.Net: url=%s" % (self.url))
	
	def _getLoginScript(self):
		return self.path

	def requiresLogin(self, url = None):
		return False

	def performLogin(self, url = None):
		return True

	def _getVarValue(self, varstr):
		#logging.debug('_getVarValue varstr=%s' % varstr)
		vals = varstr.split('=')
		#logging.debug('vals=%s' % vals)
		retstr="".join(vals[+1:])
		#logging.debug('retstr=%s' % retstr)
		if retstr.startswith(' '):
			retstr = retstr[1:]
		if retstr.endswith(';'):
			retstr = retstr[:-1]
		return retstr
	
	def _splitCrossover(self, subject):
		if "Crossover" in subject:
			self._addSubject ("Crossover")
			logging.debug('Crossover=%s' % subject)
			if subject.find(' and ') != -1:
				words = subject.split(' ')
				logging.debug('words=%s' % words)
				subj = ''
				for s in words:
					if s in "and Crossover":
						if len(subj) > 0:
							self._addSubject(subj)
						subj = ''
					else:
						if len(subj) > 0:
							subj = subj + ' '
						subj = subj + s
				if len(subj) > 0:
					self._addSubject(subj)
			else:
				self._addSubject(subject)
		else:
			self._addSubject(subject)
		return True

	def _splitGenre(self, subject):
		if len(subject) > 0:
			words = subject.split('/')
			logging.debug('words=%s' % words)
			for subj in words:
			    if len(subj) > 0:
				self._addSubject(subj)
		return True

	def _addSubject(self, subject):
		subj = subject.upper()
		for s in self.subjects:
			if s.upper() == subj:
				return False

		self.subjects.append(subject)
		return True

	def _addCharacter(self, character):
		chara = character.upper()
		for c in self.storyCharacters:
			if c.upper() == chara:
				return False
		self.storyCharacters.append(character)
		return True

	def _fetchUrl(self, url):
		if not appEngine:
			return self.opener.open(url).read().decode('utf-8')
		else:
			return googlefetch(url).content
	
	def extractIndividualUrls(self):
		data = self._fetchUrl(self.url)
		d2 = re.sub('&\#[0-9]+;', ' ', data)
		soup = bs.BeautifulStoneSoup(d2)
		allA = soup.findAll('a')
		for a in allA:
			if 'href' in a._getAttrMap() and a['href'].find('/u/') != -1:
				self.authorName = a.string
				(u1, u2, self.authorId, u3) = a['href'].split('/')
				logging.debug('self.authorId=%s self.authorName=%s' % (self.authorId, self.authorName))

		urls = []
		
		metas = soup.findAll ('meta', {'name' : 'description'})
		if metas is not None:
			for meta in metas:
				if 'content' in meta._getAttrMap():
					self.storyDescription = str(meta['content'])
					logging.debug('self.storyDescription=%s' % self.storyDescription)
					
					title=meta.find('title')
					logging.debug('title=%s' % title.string)
					tt = title.string.split(',')
					if tt is not None:
						if len(tt) > 0:
							self.storyName = tt[0]
							self.outputName = self.storyName.replace(" ", "_") + '-fpcom_' + self.storyId
							logging.debug('self.storyId=%s, self.storyName=%s, self.outputName=%s' % (self.storyId, self.storyName, self.outputName))
						if len(tt) > 1:
							tt1 = tt[1].split(' - ')
							if tt1 is not None and len(tt1) > 0:
								self.category = tt1[0].strip()
								logging.debug('self.category=%s' % self.category)
								cc = self.category.split(' ')
								for cc1 in cc:
									if cc1 is not None and cc1 != 'a':
										if cc1 == 'fanfic':
											self._addSubject('FanFiction')
										else:
											self._addSubject(cc1)
								logging.debug('self.subjects=%s' % self.subjects)
								

		fidochap = soup.find('form', {'name':'fidochap'})
		sl = fidochap.find('select', {'title':'chapter navigation'})
		logging.debug('sl=%s' % sl )
		urlstory = ''
		if 'onchange' in sl._getAttrMap():
			ocs = sl['onchange'].split('\'')
			logging.debug('ocs=%s' % ocs)
			if ocs is not None and len(ocs) > 3:
				urlstory = ocs[3]
				logging.debug('urlstory=%s' % urlstory)
			
		numchapters = 0
		opts = sl.findAll('option')
		for o in opts:
			if 'value' in o._getAttrMap():
				url = 'http://' + self.host + '/s/' + self.storyId  + '/' + o['value'] + urlstory
				logging.debug('URL=%s, Title=%s' % (url, o.string))
				urls.append((url, o.string))
				numchapters = numchapters + 1
		
		if numchapters == 0:
			numchapters = 1
			url = 'http://' + self.host + '/s/' + self.storyId  + '/1' +  urlstory
			logging.debug('URL=%s, Title=%s' % (url, self.storyName))
			urls.append((url, self.storyName))
			
		self.numChapters = str(numchapters)
		logging.debug('self.numChapters=%s' % self.numChapters)
		logging.debug('urls=%s' % urls)
		
		self.genre = ''
		tds = fidochap.findAll('td')
		for td in tds:
			tdb = td.find('b')
			if tdb is not None and tdb.string == self.storyName:
				tdas = td.findAll('a')
				for tda in tdas:
					ss = tda.string
					if ss is not None:
						if len(self.genre) > 0:
							self.genre = self.genre + ', '
						self.genre = self.genre + ss
						self._addSubject(ss)
				logging.debug('self.genre=%s' % self.genre)
				logging.debug('self.subjects=%s' % self.subjects)
			tda = td.find ('a')
			if tda is not None and tda.string.find('Rated:') != -1:
				tdas = re.split ("<[^>]+>", str(td).replace('\n','').replace('&nbsp;',' '))
				if tdas is not None:
					ll = len(tdas)
					if ll > 2:
						ss = tdas[2].split(': ')
						if ss is not None and len(ss) > 1:
							self.storyRating = ss[1]
							logging.debug('self.storyRating=%s' % self.storyRating)
					if ll > 3:
						ss = tdas[3].split(' - ')
						if ss is not None:
							lls = len(ss)
							if lls > 1:
								language = ss[1]
								logging.debug('language=%s' % language)
							if lls > 2:
								self.category = ss[2]
								logging.debug('self.category=%s' % self.category)
								sgs = self.category.split('/')
								for sg in sgs:
									self._addSubject(sg)
								logging.debug('self.subjects=%s' % self.subjects)
							if lls > 3 and ss[3].strip() == 'Reviews:' and ll > 4:
								reviews = tdas[4] 
								logging.debug('reviews=%s' % reviews)
					if ll > 5:
						ss = tdas[5].split(' - ')
						if ss is not None:
							lls = len(ss)
							if lls > 1:
								sds = ss[1].split(': ')
								logging.debug('sds=%s' % sds)
								if sds is not None and len(sds) > 1 and sds[0] == 'Published':
									self.storyPublished = datetime.datetime.fromtimestamp(time.mktime(time.strptime(sds[1].strip(' '), "%m-%d-%y")))
									logging.debug('self.storyPublished=%s' % self.storyPublished)
							lls = len(ss)
							if lls > 2:
								sds = ss[2].split(': ')
								logging.debug('sds=%s' % sds)
								if sds is not None and len(sds) > 1 and sds[0] == 'Updated':
									self.storyUpdated = datetime.datetime.fromtimestamp(time.mktime(time.strptime(sds[1].strip(' '), "%m-%d-%y")))
									logging.debug('self.storyUpdated=%s' % self.storyUpdated)
									


		self.uuid = 'urn:uuid:' + self.host + '-a.' + self.authorId + '-s.' + self.storyId
		self.authorURL = 'http://' + self.host + '/u/' + self.authorId
		logging.debug('self.uuid=%s' % self.uuid)

		return urls
	
	def getText(self, url):
		time.sleep( 2.0 )
		data = self._fetchUrl(url)
		lines = data.split('\n')
		
		textbuf = ''
		emit = False
		
		olddata = data
		try:
			data = data.decode('utf8')
		except:
			data = olddata
		
		try:
			soup = bs.BeautifulStoneSoup(data)
		except:
			logging.info("Failed to decode: <%s>" % data)
			soup = None
		div = soup.find('div', {'id' : 'storytext'})
		if None == div:
			logging.error("Error downloading Chapter: %s" % url)
			exit (20)
			return '<html/>'
			
		return div.__str__('utf8')
					
	def setLogin(self, login):
		self.login = login

	def setPassword(self, password):
		self.password = password

	def getHost(self):
		logging.debug('self.host=%s' % self.host)
		return self.host

	def getStoryURL(self):
		logging.debug('self.url=%s' % self.url)
		return self.url

	def getUUID(self):
		logging.debug('self.uuid=%s' % self.uuid)
		return self.uuid

	def getOutputName(self):
		logging.debug('self.storyId=%s, self.storyName=%s self.outputName=%s' % (self.storyId, self.storyName, self.outputName))
		return self.outputName

	def getAuthorName(self):
		logging.debug('self.authorName=%s' % self.authorName)
		return self.authorName

	def getAuthorId(self):
		logging.debug('self.authorId=%s' % self.authorId)
		return self.authorId

	def getAuthorURL(self):
		logging.debug('self.authorURL=%s' % self.authorURL)
		return self.authorURL

	def getStoryId(self):
		logging.debug('self.storyId=%s' % self.storyId)
		return self.storyId

	def getStoryName(self):
		logging.debug('self.storyName=%s' % self.storyName)
		return self.storyName

	def getStoryDescription(self):
		logging.debug('self.storyDescription=%s' % self.storyDescription)
		return self.storyDescription

	def getStoryPublished(self):
		logging.debug('self.storyPublished=%s' % self.storyPublished)
		return self.storyPublished

	def getStoryCreated(self):
		self.storyCreated = datetime.datetime.now()
		logging.debug('self.storyCreated=%s' % self.storyCreated)
		return self.storyCreated

	def getStoryUpdated(self):
		logging.debug('self.storyUpdated=%s' % self.storyUpdated)
		return self.storyUpdated

	def getLanguage(self):
		logging.debug('self.language=%s' % self.language)
		return self.language

	def getLanguageId(self):
		logging.debug('self.languageId=%s' % self.languageId)
		return self.languageId

	def getSubjects(self):
		logging.debug('self.subjects=%s' % self.authorName)
		return self.subjects

	def getPublisher(self):
		logging.debug('self.publisher=%s' % self.publisher)
		return self.publisher

	def getNumChapters(self):
		logging.debug('self.numChapters=%s' % self.numChapters)
		return self.numChapters

	def getNumWords(self):
		logging.debug('self.numWords=%s' % self.numWords)
		return self.numWords

	def getCategory(self):
		logging.debug('self.category=%s' % self.category)
		return self.category

	def getGenre(self):
		logging.debug('self.genre=%s' % self.genre)
		return self.genre

	def getStoryStatus(self):
		logging.debug('self.storyStatus=%s' % self.storyStatus)
		return self.storyStatus

	def getStoryRating(self):
		logging.debug('self.storyRating=%s' % self.storyRating)
		return self.storyRating

	def getStoryUserRating(self):
		logging.debug('self.storyUserRating=%s' % self.storyUserRating)
		return self.storyUserRating

	def getPrintableUrl(self, url):
		pass

	def getStoryCharacters(self):
		logging.debug('self.storyCharacters=%s' % self.storyCharacters)
		return self.storyCharacters
	
	def getStorySeries(self):
		logging.debug('self.storySeries=%s' % self.storySeries)
		return self.storySeries
		
class FFA_UnitTests(unittest.TestCase):
	def setUp(self):
		logging.basicConfig(level=logging.DEBUG)
		pass
	
	def testChaptersAuthStory(self):
		f = FFNet('http://www.fanfiction.net/s/5257563/1')
		f.extractIndividualUrls()
		
		self.assertEquals('Beka0502', f.getAuthorName())
		self.assertEquals("Draco's Redemption", f.getStoryName())

	def testChaptersCountNames(self):
		f = FFNet('http://www.fanfiction.net/s/5257563/1')
		urls = f.extractIndividualUrls()
		
		self.assertEquals(10, len(urls))
	
	def testGetText(self):
		url = 'http://www.fanfiction.net/s/5257563/1'
		f = FFNet(url)
		text = f.getText(url)
		self.assertTrue(text.find('He was just about to look at some photos when he heard a crack') != -1)
	
	def testBrokenWands(self):
		url = 'http://www.fanfiction.net/s/1527263/30/Harry_Potter_and_Broken_Wands'
		f = FFNet(url)
		text = f.getText(url)
		
		urls = f.extractIndividualUrls()
	
	def testFictionPress(self):
		url = 'http://www.fictionpress.com/s/2725180/1/Behind_This_Facade'
		f = FFNet(url)
		urls = f.extractIndividualUrls()
		
		self.assertEquals('Behind This Facade', f.getStoryName())
		self.assertEquals('IntoxicatingMelody', f.getAuthorName())
	
		text = f.getText(url)
		self.assertTrue(text.find('Kale Resgerald at your service" He answered, "So, can we go now? Or do you want to') != -1)
if __name__ == '__main__':
	unittest.main()

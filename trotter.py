#!/usr/bin/python

"""Daytrotter-trotter.

Trots on over to daytrotter.com and grabs the latest Daytrotter Session .mp3s.
By default, remembers the last session you downloaded and only gets newer ones;
also accepts specific date-ranges and downloads all sessions in that range.
Songs are saved in the songs/ subdirectory, which will be created in the same
directory that trotter.py lives in.

Note: The trotter uses daytrotter.com's RSS feed to do its magic, and that feed
	seems to only list the most recent ~29 sessions at any given time, so
	you're basically SOL if you fall more than 29 sessions behind.
	It won't crash or anything, but if you specify a date range that contains
	dates older than 29 sessions ago, don't expect it to find those sessions.
	This may be improved upon in a future release, but don't hold your breath :)
	
Note 2: If you'd like to reset the "last downloaded session" marker the trotter
saved for you, just delete the log.txt file in this directory.

Usage: python trotter.py [options]

Options:
	-s ..., --start=...		start date
	-e ..., --end=...		end date
	-h, --help			show this help
	
Examples:
	trotter.py				fetches any new sessions 
	trotter.py -s 06/04/09			all since june 4, 2009 (inclusive)
	trotter.py -e 06/07/09			all up to june 7, 2009 (inclusive)
	trotter.py -s 06/04/09 -e 06/07/09	from june 4 to june 7 09 (inclusive)
"""

__author__ = "JR Heard (jrheard@cs.stanford.edu)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2009/06/07 13:06:58 $"
__copyright__ = "Copyright (c) 2009 JR Heard"
__license__ = "Python"


from sgmllib import SGMLParser
import feedparser, urllib
import datetime, dateutil.parser
import re, os, sys, getopt

class DaytrotterParser(SGMLParser):
	"""A simple parser class, used to find <a> tags in Daytrotter Sessions pages
	in order to see if they contain links to .mp3s. """
	
	def reset(self):
		self.song_urls = []
		SGMLParser.reset(self)
	
	def start_a(self, attributes):
		"""Search through a found <a> tag's attributes for an .mp3 URL"""
		
		for name, value in attributes:
			if name == "href" and re.search("\.mp3", value):
				self.song_urls.append(value)
	
	def get_song_urls(self):
		"""Returns the list of found song URLs."""
		return self.song_urls
	
	def parse(self, s):
		self.feed(s)
		self.close()

###########################
	
def grab_songs_from_session(session):
	"""Downloads the songs from the session it's handed"""
	
	print "grabbing", session.title, "..."
	sock = urllib.urlopen(session.link)
	html = sock.read()
	sock.close()
	
	parser = DaytrotterParser()
	parser.parse(html)
	parser.close()
	
	urls = parser.get_song_urls()
	
	for url in urls:
		filename = url.split("/")[-1]
		print "\tgrabbing", filename
		urllib.urlretrieve(url, filename)


def parseDate(date):
	"""Takes a date string, parses it, returns a datetime.date"""
	
	return dateutil.parser.parse(date).date()


def session_in_daterange(session, start, end):
	"""Returns true if the session is between the start and end dates, inclusive; false otherwise"""
	
	updated = parseDate(session.updated)
	return start <= updated and end >= updated


def should_update_logfile(sessions):
	"""Returns true if the logfile should be updated to reflect this trot, false otherwise"""
	
	try:
		last_updated = parseDate(file("log.txt").read())
		return last_updated < parseDate(sessions[0].updated)
	except:
		return True # the logfile didn't exist, so we should create one

def grab_sessions(start, end):
	"""Grabs all sessions between the start and end dates, inclusive"""
	
	print "grabbing all sessions between", start, "and", end, "..."
	
	feed = feedparser.parse('http://www.daytrotter.com/rss/recentlyadded.aspx')
	
	try:
		os.mkdir("songs")
	except:
		pass # dir already existed, which is fine
		
	os.chdir("songs")
	
	sessions = [session for session in feed.entries if session_in_daterange(session, start, end)]
	for session in sessions:
		grab_songs_from_session(session)

	print "done!"
	os.chdir("..") # back out so's we don't keep the logfile in the same dir as the songs
	
	if(sessions and should_update_logfile(sessions)):
		logfile = open("log.txt", "w")
		logfile.write(sessions[0].updated) # log the most recent downloaded session for next time
		logfile.close()
		print "\nmarked your place at", sessions[0].updated, "for next time."


def usage():
	print __doc__
 
	
def main(argv):
	start = None
	end = datetime.date.today()
	
	try:
		opts, args = getopt.getopt(argv, "hs:e:", ["help", "start=", "end="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-s", "--start"):
			start = parseDate(arg[1:])
		elif opt in ("-e", "--end"):
			end = parseDate(arg[1:])
	
	if not start: # if start wasn't set, set it
		try:
			start = parseDate(file("log.txt").read()) # grab the start date from the log file
			start += datetime.timedelta(days=1) # skip ahead one day, no need to re-download this session
		except: 
			start = datetime.date.today() + datetime.timedelta(days=-365) # grab whatever we can
	
	grab_sessions(start, end) # okay, go get 'em

if __name__ == "__main__":
	main(sys.argv[1:])

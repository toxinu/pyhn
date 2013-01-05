"""
hn-api is a simple, ad-hoc Python API for Hacker News.
======================================================

hn-api is released under the Simplified BSD License:

Copyright (c) 2010, Scott Jackson
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY SCOTT JACKSON ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SCOTT JACKSON OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Scott Jackson.


"""

from BeautifulSoup import BeautifulSoup
import urllib2
import re

class HNException(Exception):
    """
    HNException is exactly the same as a plain Python Exception.

    The HNException class exists solely so that you can identify
    errors that come from HN as opposed to from your application.
    """
    pass

class HackerNewsAPI:
    """
    The class for slicing and dicing the HTML and turning it into HackerNewsStory objects.
    """
    numberOfStoriesOnFrontPage = 0

    def getSource(self, url):
        """
        Returns the HTML source code for a URL.
        """
        try:
            f = urllib2.urlopen(url)
            source = f.read()
            f.close()
            return source.decode('utf-8')
        except urllib2.URLError:
            raise HNException("Error getting source from " + url + ". Your internet connection may have something funny going on, or you could be behind a proxy.")

    def getStoryNumber(self, source):
        """
        Parses HTML and returns the number of a story.
        """
        numberStart = source.find('>') + 1
        numberEnd = source.find('.')
        return int(source[numberStart:numberEnd])

    def getStoryURL(self, source):
        """
        Gets the URL of a story.
        """
        URLStart = source.find('href="') + 6
        URLEnd = source.find('">', URLStart)
        url = source[URLStart:URLEnd]
        # Check for "Ask HN" links.
        if url[0:4] == "item": # "Ask HN" links start with "item".
            url = "http://news.ycombinator.com/" + url

        # Change "&amp;" to "&"
        url = url.replace("&amp;", "&")

        # Remove 'rel="nofollow' from the end of links, since they were causing some bugs.
        if url[len(url)-13:] == "rel=\"nofollow":
            url = url[:len(url)-13]

        # Weird hack for URLs that end in '" '. Consider removing later if it causes any problems.
        if url[len(url)-2:] == "\" ":
            url = url[:len(url)-2]
        return url

    def getStoryDomain(self, source):
        """
        Gets the domain of a story.
        """
        domainStart = source.find('comhead">') + 10
        domainEnd = source.find('</span>')
        domain = source[domainStart:domainEnd]
        # Check for "Ask HN" links.
        if domain[0] == '=':
            return "http://news.ycombinator.com"
        return "http://" + domain[1:len(domain)-2]

    def getStoryTitle(self, source):
        """
        Gets the title of a story.
        """
        titleStart = source.find('>', source.find('>')+1) + 1
        titleEnd = source.find('</a>')
        title = source[titleStart:titleEnd]
        title = title.lstrip()  # Strip trailing whitespace characters.
        return title

    def getStoryScore(self, source):
        """
        Gets the score of a story.
        """
        scoreStart = source.find('>', source.find('>')+1) + 1
        scoreEnd = source.find(' ', scoreStart)
        score = source[scoreStart:scoreEnd]
        if not score.isdigit():
            return -1
        return int(score)

    def getSubmitter(self, source):
        """
        Gets the HN username of the person that submitted a story.
        """
        submitterStart = source.find('user?id=')
        realSubmitterStart = source.find('=', submitterStart) + 1
        submitterEnd = source.find('"', realSubmitterStart)
        return source[realSubmitterStart:submitterEnd]

    def getCommentCount(self, source):
        """
        Gets the comment count of a story.
        """
        commentStart = source.find('item?id=')
        commentCountStart = source.find('>', commentStart) + 1
        commentEnd = source.find('</a>', commentStart)
        commentCountString = source[commentCountStart:commentEnd]
        if commentCountString == "discuss":
            return 0
        elif commentCountString == "":
            return 0
        else:
            commentCountString = commentCountString.split(' ')[0]
            return int(commentCountString)

    def getPublishedTime(self, source):
        """
        Gets the published time ago
        """
        p = re.compile(r'\d{1,} (minutes|minute|hours|hour|day|days) ago')
        results = p.search(source)
        return results.group()

    def getHNID(self, source):
        """
        Gets the Hacker News ID of a story.
        """
        idPrefix = 'score_'
        urlStart = source.find(idPrefix) + len(idPrefix)
        if urlStart <= len(idPrefix):
            return -1
        urlEnd = source.find('"', urlStart)
        return int(source[urlStart:urlEnd])

    def getCommentsURL(self, source):
        """
        Gets the comment URL of a story.
        """
        return "http://news.ycombinator.com/item?id=" + str(self.getHNID(source))

    def getStories(self, source):
        """
        Looks at source, makes stories from it, returns the stories.
        """
        self.numberOfStoriesOnFrontPage = source.count("span id=score")
        # Create the empty stories.
        newsStories = []
        for i in range(0, self.numberOfStoriesOnFrontPage):
            story = HackerNewsStory()
            newsStories.append(story)

        soup = BeautifulSoup(source)
        # Gives URLs, Domains and titles.
        story_details = soup.findAll("td", {"class" : "title"})
        # Gives score, submitter, comment count and comment URL.
        story_other_details = soup.findAll("td", {"class" : "subtext"})

        # Get story numbers.
        storyNumbers = []
        for i in range(0,len(story_details) - 1, 2):
            story = str(story_details[i]) # otherwise, story_details[i] is a BeautifulSoup-defined object.
            storyNumber = self.getStoryNumber(story)
            storyNumbers.append(storyNumber)

        storyURLs = []
        storyDomains = []
        storyTitles = []
        storyScores = []
        storySubmitters = []
        storyCommentCounts = []
        storyCommentURLs = []
        storyPublishedTime = []
        storyIDs = []

        for i in range(1, len(story_details), 2): # Every second cell contains a story.
            story = str(story_details[i])
            storyURLs.append(self.getStoryURL(story))
            storyDomains.append(self.getStoryDomain(story))
            storyTitles.append(self.getStoryTitle(story))

        for s in story_other_details:
            story = str(s)
            storyScores.append(self.getStoryScore(story))
            storySubmitters.append(self.getSubmitter(story))
            storyCommentCounts.append(self.getCommentCount(story))
            storyCommentURLs.append(self.getCommentsURL(story))
            storyPublishedTime.append(self.getPublishedTime(story))
            storyIDs.append(self.getHNID(story))


        # Associate the values with our newsStories.
        for i in range(0, self.numberOfStoriesOnFrontPage):
            newsStories[i].number = storyNumbers[i]
            newsStories[i].URL = storyURLs[i]
            newsStories[i].domain = storyDomains[i]
            newsStories[i].title = storyTitles[i]
            newsStories[i].score = storyScores[i]
            newsStories[i].submitter = storySubmitters[i]
            newsStories[i].commentCount = storyCommentCounts[i]
            newsStories[i].commentsURL = storyCommentURLs[i]
            newsStories[i].publishedTime = storyPublishedTime[i]
            newsStories[i].id = storyIDs[i]

            if newsStories[i].id < 0:
                idStart = newsStories[i].URL.find('item?id=') + 8
                newsStories[i].commentsURL = ''
                newsStories[i].submitter = 'Y Combinator'

        return newsStories

    ##### End of internal methods. #####

    # The following methods could be turned into one method with
    # an argument that switches which page to get stories from,
    # but I thought it would be simplest if I kept the methods
    # separate.

    def getTopStories(self):
        """
        Gets the top stories from Hacker News.
        """
        sourceNew1 = self.getSource("http://news.ycombinator.com/news")
        sourceNew2 = self.getSource("http://news.ycombinator.com/news2")
        storiesNew1  = self.getStories(sourceNew1)
        storiesNew2  = self.getStories(sourceNew2)
        stories = storiesNew1 + storiesNew2
        return stories

    def getNewestStories(self):
        """
        Gets the newest stories from Hacker News.
        """
        source = self.getSource("http://news.ycombinator.com/newest")
        stories  = self.getStories(source)
        return stories

    def getBestStories(self):
        """
        Gets the "best" stories from Hacker News.
        """
        source = self.getSource("http://news.ycombinator.com/best")
        stories  = self.getStories(source)
        return stories

    def getPageStories(self, pageId):
        """
        Gets the pageId stories from Hacker News.
        """
        source = self.getSource("http://news.ycombinator.com/x?fnid=%s" % pageId)
        stories  = self.getStories(source)
        return stories

class HackerNewsStory:
    """
    A class representing a story on Hacker News.
    """
    id = 0      # The Hacker News ID of a story.
    number = -1 # What rank the story is on HN.
    title = ""  # The title of the story.
    domain = "" # The website the story is from.
    URL = ""    # The URL of the story.
    score = -1  # Current score of the story.
    submitter = ""  # The person that submitted the story.
    commentCount = -1   # How many comments the story has.
    commentsURL = ""    # The HN link for commenting (and upmodding).
    publishedTime = ""  # The time sinc story was published

    def printDetails(self):
        """
        Prints details of the story.
        """
        print str(self.number) + ": " + self.title
        print "URL: " + self.URL
        print "domain: " + self.domain
        print "score: " + str(self.score) + " points"
        print "submitted by: " + self.submitter
        print "sinc %s" + self.publishedTime
        print "# of comments: " + str(self.commentCount)
        print "'discuss' URL: " + self.commentsURL
        print "HN ID: " + str(self.id)
        print " "


class HackerNewsUser:
    """
    A class representing a user on Hacker News.
    """
    karma = -10000  # Default value. I don't think anyone really has -10000 karma.
    name = ""   # The user's HN username.
    userPageURL = ""    # The URL of the user's 'user' page.
    threadsPageURL = "" # The URL of the user's 'threads' page.

    def __init__(self, username):
        """
        Constructor for the user class.
        """
        self.name = username
        self.userPageURL = "http://news.ycombinator.com/user?id=" + self.name
        self.threadsPageURL = "http://news.ycombinator.com/threads?id=" + self.name
        self.refreshKarma()


    def refreshKarma(self):
        """
        Gets the karma count of a user from the source of their 'user' page.
        """
        hn = HackerNewsAPI()
        source = hn.getSource(self.userPageURL)
        karmaStart = source.find('<td valign=top>karma:</td><td>') + 30
        karmaEnd = source.find('</td>', karmaStart)
        karma = source[karmaStart:karmaEnd]
        if karma is not '':
            self.karma = int(karma)
        else:
            raise HNException("Error getting karma for user " + self.name)
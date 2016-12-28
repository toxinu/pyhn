"""
hn-api is a simple, ad-hoc Python API for Hacker News.
======================================================

hn-api is released under the Simplified BSD License:

Copyright (c) 2010, Scott Jackson
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY SCOTT JACKSON ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL SCOTT JACKSON OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are
those of the authors and should not be interpreted as representing official
policies, either expressed or implied, of Scott Jackson.


"""
import re
import sys

import requests
from bs4 import BeautifulSoup

PY3 = False
if sys.version_info.major == 3:
    PY3 = True

if PY3:
    from urllib.parse import urljoin
    from urllib.parse import urlparse
else:
    from urlparse import urljoin
    from urlparse import urlparse

HEADERS = {
    'User-Agent': (
        "Pyhn (Hacker news command line client) - "
        "https://github.com/toxinu/pyhn")}


class HNException(Exception):
    """
    HNException is exactly the same as a plain Python Exception.

    The HNException class exists solely so that you can identify
    errors that come from HN as opposed to from your application.
    """
    pass


class HackerNewsAPI:
    """
    The class for slicing and dicing the HTML and turning
    it into HackerNewsStory objects.
    """
    number_of_stories_on_front_page = 0

    def get_source(self, url):
        """
        Returns the HTML source code for a URL.
        """
        try:
            r = requests.get(url, headers=HEADERS)
            if r:
                return r.text
        except Exception:
            raise HNException(
                "Error getting source from " + url +
                ". Your internet connection may have something "
                "funny going on, or you could be behind a proxy.")

    def get_story_number(self, source):
        """
        Parses HTML and returns the number of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        span = bs.find('span', attrs={'class': 'rank'})
        if span.string:
            number = span.string.replace('.', '')
            return int(number)

    def get_story_url(self, source):
        """
        Gets the URL of a story.
        """
        url_start = source.find('href="') + 6
        url_end = source.find('">', url_start)
        url = source[url_start:url_end]
        # Check for "Ask HN" links.
        if url[0:4] == "item":  # "Ask HN" links start with "item".
            url = "https://news.ycombinator.com/" + url

        # Change "&amp;" to "&"
        url = url.replace("&amp;", "&")

        # Remove 'rel="nofollow' from the end of links,
        # since they were causing some bugs.
        if url[len(url) - 13:] == "rel=\"nofollow":
            url = url[:len(url) - 13]

        # Weird hack for URLs that end in '" '.
        # Consider removing later if it causes any problems.
        if url[len(url) - 2:] == "\" ":
            url = url[:len(url) - 2]
        return url

    def get_story_domain(self, source):
        """
        Gets the domain of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        url = bs.find('a').get('href')
        url_parsed = urlparse(url)
        if url_parsed.netloc:
            return url
        return urljoin('https://news.ycombinator.com', url)

    def get_story_title(self, source):
        """
        Gets the title of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        title = bs.find('td', attrs={'class': 'title'}).text
        title = title.strip()
        return title

    def get_story_score(self, source):
        """
        Gets the score of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        tags = bs.find_all('span', {'class': 'score'})
        if tags:
            score = tags[0].text.split(u'\xa0')
            if not score or not score[0].isdigit():
                score = tags[0].text.split(' ')
            if score and score[0].isdigit():
                return int(score[0])

    def get_submitter(self, source):
        """
        Gets the HN username of the person that submitted a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        tags = bs.find_all('a', {'class': 'hnuser'})
        if tags:
            return tags[0].text

    def get_comment_count(self, source):
        """
        Gets the comment count of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        comments = bs.find_all('a', text=re.compile('comment'))
        if comments:
            comments = comments[0].text
            separator = u'\xc2\xa0'
            if separator in comments:
                comments = comments.split(separator)[0]
            else:
                comments = comments.split(u'\xa0')[0]
            try:
                return int(comments)
            except ValueError:
                return None

        comments = bs.find_all('a', text=re.compile('discuss'))
        if comments:
            return 0

    def get_published_time(self, source):
        """
        Gets the published time ago
        """
        p = re.compile(
            r'\d{1,}\s(minutes|minute|hours|hour|day|days)\sago', flags=re.U)

        if not PY3:
            source = source.decode('utf-8')

        results = p.search(source)
        if results:
            return results.group()

    def get_hn_id(self, source):
        """
        Gets the Hacker News ID of a story.
        """
        bs = BeautifulSoup(source, "html.parser")
        hn_id = bs.find_all('a', {'href': re.compile('item\?id=')})
        if hn_id:
            hn_id = hn_id[0].get('href')
            if hn_id:
                hn_id = hn_id.split('item?id=')[-1]
                if hn_id.isdigit():
                    return int(hn_id)

    def get_comments_url(self, source):
        """
        Gets the comment URL of a story.
        """
        return "https://news.ycombinator.com/item?id=" + str(
            self.get_hn_id(source))

    def get_stories(self, source):
        """
        Looks at source, makes stories from it, returns the stories.
        """
        """ <td align=right valign=top class="title">31.</td> """
        self.number_of_stories_on_front_page = source.count(
            'span class="rank"')

        # Create the empty stories.
        news_stories = []
        for i in range(0, self.number_of_stories_on_front_page):
            story = HackerNewsStory()
            news_stories.append(story)

        soup = BeautifulSoup(source, "html.parser")
        # Gives URLs, Domains and titles.
        story_details = soup.findAll("td", {"class": "title"})
        # Gives score, submitter, comment count and comment URL.
        story_other_details = soup.findAll("td", {"class": "subtext"})
        # Get story numbers.
        story_numbers = []
        for i in range(0, len(story_details) - 1, 2):
            # Otherwise, story_details[i] is a BeautifulSoup-defined object.
            story = str(story_details[i])
            story_number = self.get_story_number(story)
            story_numbers.append(story_number)

        story_urls = []
        story_domains = []
        story_titles = []
        story_scores = []
        story_submitters = []
        story_comment_counts = []
        story_comment_urls = []
        story_published_time = []
        story_ids = []

        # Every second cell contains a story.
        for i in range(1, len(story_details), 2):
            story = str(story_details[i])
            story_urls.append(self.get_story_url(story))
            story_domains.append(self.get_story_domain(story))
            story_titles.append(self.get_story_title(story))

        for s in story_other_details:
            story = str(s)
            story_scores.append(self.get_story_score(story))
            story_submitters.append(self.get_submitter(story))
            story_comment_counts.append(self.get_comment_count(story))
            story_comment_urls.append(self.get_comments_url(story))
            story_published_time.append(self.get_published_time(story))
            story_ids.append(self.get_hn_id(story))

        # Associate the values with our newsStories.
        for i in range(0, self.number_of_stories_on_front_page):
            news_stories[i].number = story_numbers[i]
            news_stories[i].url = story_urls[i]
            news_stories[i].domain = story_domains[i]
            news_stories[i].title = story_titles[i]
            news_stories[i].score = story_scores[i]
            news_stories[i].submitter = story_submitters[i]
            if news_stories[i].submitter:
                news_stories[i].submitter_url = (
                    "https://news.ycombinator.com/user?id={}".format(
                        story_submitters[i]))
            else:
                news_stories[i].submitter_url = None
            news_stories[i].comment_count = story_comment_counts[i]
            news_stories[i].comments_url = story_comment_urls[i]
            news_stories[i].published_time = story_published_time[i]
            news_stories[i].id = story_ids[i]

            if news_stories[i].id < 0:
                news_stories[i].url.find('item?id=') + 8
                news_stories[i].comments_url = ''
                news_stories[i].submitter = None
                news_stories[i].submitter_url = None

        return news_stories

    def get_more_link(self, source):
        soup = BeautifulSoup(source, "html.parser")
        more_a = soup.findAll("a", {"rel": "nofollow"}, text="More")
        if more_a:
            return urljoin('https://news.ycombinator.com/', more_a[0]['href'])
        return None

    # #### End of internal methods. #####

    # The following methods could be turned into one method with
    # an argument that switches which page to get stories from,
    # but I thought it would be simplest if I kept the methods
    # separate.

    def get_jobs_stories(self, extra_page=1):
        stories = []
        source_latest = self.get_source("https://news.ycombinator.com/jobs")
        stories += self.get_stories(source_latest)
        for i in range(1, extra_page + 2):
            get_more_link = self.get_more_link(source_latest)
            if not get_more_link:
                break
            source_latest = self.get_source(get_more_link)
            stories += self.get_stories(source_latest)

        return stories

    def get_ask_stories(self, extra_page=1):
        stories = []
        for i in range(1, extra_page + 2):
            source = self.number_of_stories_on_front_page(
                "https://news.ycombinator.com/ask?p=%s" % i)
            stories += self.get_stories(source)
        return stories

    def get_show_newest_stories(self, extra_page=1):
        stories = []
        source_latest = self.get_source("https://news.ycombinator.com/shownew")
        stories += self.get_stories(source_latest)
        for i in range(1, extra_page + 2):
            get_more_link = self.get_more_link(source_latest)
            if not get_more_link:
                break
            source_latest = self.get_source(get_more_link)
            stories += self.get_stories(source_latest)
        return stories

    def get_show_stories(self, extra_page=1):
        stories = []
        source_latest = self.get_source("https://news.ycombinator.com/show")
        stories += self.get_stories(source_latest)
        for i in range(1, extra_page + 2):
            get_more_link = self.get_more_link(source_latest)
            if not get_more_link:
                break
            source_latest = self.get_source(get_more_link)
            stories += self.get_stories(source_latest)
        return stories

    def get_top_stories(self, extra_page=1):
        """
        Gets the top stories from Hacker News.
        """
        stories = []
        for i in range(1, extra_page + 2):
            source = self.get_source(
                "https://news.ycombinator.com/news?p=%s" % i)
            stories += self.get_stories(source)
        return stories

    def get_newest_stories(self, extra_page=1):
        """
        Gets the newest stories from Hacker News.
        """
        stories = []
        source_latest = self.get_source("https://news.ycombinator.com/newest")
        stories += self.get_stories(source_latest)
        for i in range(1, extra_page + 2):
            get_more_link = self.get_more_link(source_latest)
            if not get_more_link:
                break
            source_latest = self.get_source(get_more_link)
            stories += self.get_stories(source_latest)
        return stories

    def get_best_stories(self, extra_page=1):
        """
        Gets the "best" stories from Hacker News.
        """
        stories = []
        for i in range(1, extra_page + 2):
            source_latest = self.get_source(
                "https://news.ycombinator.com/best?p=%s" % i)
            stories += self.get_stories(source_latest)
        return stories

    def get_page_stories(self, pageId):
        """
        Gets the pageId stories from Hacker News.
        """
        source = self.get_source(
            "https://news.ycombinator.com/x?fnid=%s" % pageId)
        stories = self.get_stories(source)
        return stories


class HackerNewsStory:
    """
    A class representing a story on Hacker News.
    """
    id = 0         # The Hacker News ID of a story.
    number = None  # What rank the story is on HN.
    title = ""     # The title of the story.
    domain = ""    # The website the story is from.
    url = ""       # The URL of the story.
    score = None   # Current score of the story.
    submitter = ""        # The person that submitted the story.
    comment_count = None  # How many comments the story has.
    comments_url = ""     # The HN link for commenting (and upmodding).
    published_time = ""   # The time sinc story was published

    def get_comments(self):
        url = (
            'http://hndroidapi.appspot.com/'
            'nestedcomments/format/json/id/%s' % self.id)
        try:
            r = requests.get(url, headers=HEADERS)
            self.comments = r.json()['items']
            return self.comments
        except Exception:
            raise HNException(
                "Error getting source from " + url +
                ". Your internet connection may have something funny "
                "going on, or you could be behind a proxy.")

    def print_details(self):
        """
        Prints details of the story.
        """
        print(str(self.number) + ": " + self.title)
        print("URL: %s" % self.url)
        print("domain: %s" % self.domain)
        print("score: " + str(self.score) + " points")
        print("submitted by: " + self.submitter)
        print("sinc %s" + self.published_time)
        print("of comments: " + str(self.comment_count))
        print("'discuss' URL: " + self.comments_url)
        print("HN ID: " + str(self.id))
        print(" ")


class HackerNewsUser:
    """
    A class representing a user on Hacker News.
    """
    # Default value. I don't think anyone really has -10000 karma.
    karma = -10000
    name = ""  # The user's HN username.
    user_page_url = ""  # The URL of the user's 'user' page.
    threads_page_url = ""  # The URL of the user's 'threads' page.

    def __init__(self, username):
        """
        Constructor for the user class.
        """
        self.name = username
        self.user_page_url = (
            "https://news.ycombinator.com/user?id=" + self.name)
        self.threads_page_url = (
            "https://news.ycombinator.com/threads?id=%s" % self.name)
        self.refresh_karma()

    def refresh_karma(self):
        """
        Gets the karma count of a user from the source of their 'user' page.
        """
        hn = HackerNewsAPI()
        source = hn.get_source(self.user_page_url)
        karma_start = source.find('<td valign=top>karma:</td><td>') + 30
        karma_end = source.find('</td>', karma_start)
        karma = source[karma_start:karma_end]
        if karma is not '':
            self.karma = int(karma)
        else:
            raise HNException("Error getting karma for user " + self.name)

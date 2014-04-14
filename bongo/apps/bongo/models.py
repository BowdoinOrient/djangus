from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime
import nltk.data
import re


""" Series and Issues are helpful for grouping and archiving
Posts. Every post must belong to one Issue, but can be in many series.
Also sections are obviously a thing we do.
"""

class Series (models.Model):  # series is the singular, which may confuse django
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Volume (models.Model):
    volume_number = models.IntegerField()
    volume_year_start = models.IntegerField()
    volume_year_end = models.IntegerField()

    def __unicode__(self):
        return self.volume_number


class Issue (models.Model):
    issue_date = models.DateField()  # friday, friday, this better validate to a friday
    issue_number = models.IntegerField()
    volume = models.ForeignKey(Volume)

    def __unicode__(self):
        return self.issue_number


class Section (models.Model):
    sections = (
        ("news", "News"),
        ("features", "Features"),
        ("ae", "Arts & Entertainment"),
        ("opinion", "Opinion"),
        ("sports", "Sports"),
    )
    section = models.CharField(max_length=8, choices=sections, default="news")

    def __unicode__(self):
        return self.section


""" potential system for reccommending content. For now only a Post can have tags, but
there's potential for them to be assigned to individual content instead and then have
the Post's tags be the collection of all the content within's tags
"""
class Tag (models.Model):
    tag = models.CharField(max_length=25)

    def __unicode__(self):
        return self.tag




""" Creators own Posts. Creators might be:
    - an organization (e.g., The Editorial Board)
    - a user of Bongo (e.g., an Orient staffer)
    - not allowed to access Bongo (e.g., a columnist)

    - a photographer
    - a writer
    - a filmmaker
    - an infographicmaker
    - some combination of the above, or more
"""

class Creator(models.Model):
    # possibility this author is also a bongo user
    user = models.ForeignKey(User, null=True, blank=True)

    name = models.CharField(max_length=100)
    title = models.CharField(max_length=40, null=True, blank=True)

    twitter = models.CharField(max_length=15, null=True, blank=True)

    profpic = models.FileField(null=True, blank=True)

    def __unicode__(self):
        return self.name





""" The following models describe things a post can contain.
This is a limited subset for the time being and will expand.
"""

class Text (models.Model):
    authors = models.ManyToManyField(Creator)
    body = models.TextField()
    excerpt = models.TextField(editable=False, null=True)

    def __unicode__(self):
        return self.excerpt

    def save(self, *args, **kwargs):
        # Using NLTK here is a sledgehammer for a thumbtack, but it may be useful for tagging, too
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        excerpt = ' '.join(tokenizer.tokenize(data)[:4])
        super(Text, self).save(*args, **kwargs)


class Video (models.Model):
    filmers = models.ManyToManyField(Creator)
    staticfile = models.FileField()
    caption = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.caption[:60]


class Photo (models.Model):
    photographer = models.ForeignKey(Creator)
    staticfile = models.FileField()
    caption = models.TextField(null=True, blank=True)

    """ get_or_create a thumbnail of the specified width and height """
    def thumbnail(self, width, height):
        pass

    def __unicode__(self):
        return self.caption[:60]


class HTML (models.Model):
    designers = models.ManyToManyField(Creator)
    content = models.TextField()
    caption = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.caption[:60]




""" The following model describes things a post on the website is.
Posts are most commonly articles, but that terminology is limiting;
a post might be a stand-alone photo or an entry in a video series. 

Posts have a ManyToManyField for every type of content 
Bongo supports storing for maximum content reusability.
They also have a primary_type, which will help the frontend decide the
layout for that post (a standard article, liveblog, a photo gallery, etc.)
"""

class Post (models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)  
    # @TODO: auto-now and auto_now_add are in "accelerated deprecation" (https://code.djangoproject.com/ticket/21798)
    # and might be gone in 1.7 final. in that case a custom save() function would be needed. 

    published = models.DateTimeField()
    is_published = models.BooleanField(default=False)  # allow for drafts

    series = models.ManyToManyField(Series, null=True, blank=True)
    issue = models.ForeignKey(Issue, null=True, blank=True)  # issue might be null in the case of a web-only post
    volume = models.ForeignKey(Volume)  # volume cannot be null because it represents an academic year
    section = models.ForeignKey(Section)

    title = models.CharField(max_length=180)
    slug = models.CharField(max_length=180, editable=False, default="")  # http://en.wikipedia.org/wiki/Clean_URL#Slug
    tags = models.ManyToManyField(Tag, null=True, blank=True)

    views_local = models.IntegerField(editable=False, default=0)
    views_global = models.IntegerField(editable=False, default=0)

    creators = models.ManyToManyField(Creator, null=False)

    text = models.ManyToManyField(Text, null=True, blank=True)  # multiple text bodies in a post = liveblog
    photos = models.ManyToManyField(Photo, null=True, blank=True)
    video = models.ManyToManyField(Video, null=True, blank=True)
    html = models.ManyToManyField(HTML, null=True, blank=True)

    types = (
        ("text", "Article"),
        ("photo", "Photo(s)"),
        ("video", "Video(s)"),
        ("liveblog", "Liveblog"),
        ("html", "Interactive/Embedded"),
        ("generic", "Other")

    )

    primary_type = models.CharField(max_length=8, choices=types, default="generic")

    """ Return all of the media entities referenced by this post """
    def content(self):
        content = []

        for media in [self.text, self.photos, self.video, self.html]:
            content.append(media.all())

        return content

    def __unicode__(self):
        return self.title




""" Other miscellaneous tools """


class Alert (models.Model):
    run_from = models.DateField()
    run_through = models.DateField()

    message = models.TextField()

    urgent = models.BooleanField(default=False)

    def __unicode__(self):
        return self.message


class Advertiser (models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Ad (models.Model):
    run_from = models.DateField()
    run_through = models.DateField()

    owner = models.ForeignKey(Advertiser)

    url = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.owner + ": {} through {}".format(run_from.strftime("%x"), run_through.strftime("%x"))

class Tips (models.Model):
    content = models.TextField()
    respond_to = models.EmailField(null=True, blank=True)
    submitted_at = models.DateTimeField()
    submitted_from = models.GenericIPAddressField()
    useragent = models.TextField()

    def __unicode__(self):
        return self.content[:60]





""" For our Plancast replacement """
class Event (models.Model):
    pass





""" For our Buffer replacement """
class ScheduledPost(models.Model):
    pass





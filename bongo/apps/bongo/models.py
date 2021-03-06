from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.timezone import make_aware
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.core.cache import cache
from django.conf import settings
from itertools import chain
from bongo.apps.bongo.helpers import tagify
from hashlib import md5
import operator
import nltk.data
import requests
import logging
import json
import re
import pytz

tz = pytz.timezone('America/New_York')

logger = logging.getLogger(__name__)


""" Series and Issues are helpful for grouping and archiving
Posts. Every post must belong to one Issue, but can be in many series.
Also sections are obviously a thing we do.
"""


class Series (models.Model):  # series is the singular, which may confuse django
    class Meta:
        verbose_name_plural = "Series"

    name = models.CharField(max_length=100)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.name

    def primary_section(self):
        try:
            section_mapping = [post.section.classname() for post in self.post_set.all()]
            return section_mapping[0]
        except:
            return ""

    def preview(self):
        """Return up to three most recent entries in the series"""
        return self.post_set.all().order_by("-published")[:3]


class Volume (models.Model):
    volume_number = models.IntegerField()
    volume_year_start = models.IntegerField()
    volume_year_end = models.IntegerField()
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return str(self.volume_number)


class Issue (models.Model):
    issue_date = models.DateField()  # friday, friday, this better validate to a friday
    issue_number = models.IntegerField()
    volume = models.ForeignKey(Volume)
    scribd = models.IntegerField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    # link to a 111x142 thumbnail of the cover
    scribd_image = models.URLField(null=True, blank=True, editable=False)

    def __str__(self):
        return str(self.issue_number)

    def __init__(self, *args, **kwargs):
        super(Issue, self).__init__(*args, **kwargs)
        self.old_scribd = self.scribd

    def save(self, *args, **kwargs):
        if self.scribd and self.old_scribd != self.scribd:
            payload = {
                "method": "thumbnail.get",
                "doc_id": self.scribd,
                "format": "json",
                "api_key": settings.SCRIBD_API_KEY
            }

            api_sig = md5(
                (
                    settings.SCRIBD_API_SECRET +
                    re.sub(
                        '"|{|}',
                        '',
                        json.dumps(
                            payload,
                            separators=('', ''),
                            sort_keys=True
                        )
                    )
                ).encode('utf-8')
            ).hexdigest()
            payload['api_sig'] = api_sig

            res = requests.get("http://api.scribd.com/api", params = payload)
            if res.status_code == 200:
                try:
                    self.scribd_image = res.json()['rsp']['thumbnail_url']
                except:
                    logger.debug(
                        "bad scribd ID ({}) supplied when saving vol. {} issue {}, no thumbnail found".format(
                            self.scribd, self.volume.volume_number, self.issue_number
                        )
                    )

        super(Issue, self).save(*args, **kwargs)
        self.old_scribd = self.scribd


class Section (models.Model):
    sections = (
        ("News", "News"),
        ("Features", "Features"),
        ("A&E", "Arts & Entertainment"),
        ("Opinion", "Opinion"),
        ("Sports", "Sports"),
    )
    section = models.CharField(max_length=8, choices=sections, default="News")
    priority = models.IntegerField()
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.section

    def classname(self):
        if self.section == "A&E":
            return "artsent"
        else:
            return self.section.lower()


class Tag (models.Model):
    """ potential system for reccommending content. For now only a Post can have tags, but
    there's potential for them to be assigned to individual content instead and then have
    the Post's tags be the collection of all the content within's tags
    """

    tag = models.CharField(max_length=25)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.tag


class Job(models.Model):
    title = models.CharField(max_length=60)
    imported = models.BooleanField(default=False, editable=False)

    # returns a list of everyone with this job
    def workers(self):
        return self.creator_set.all()

    def __str__(self):
        return self.title


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
    job = models.ForeignKey(Job, null=True)
    twitter = models.CharField(max_length=15, null=True, blank=True)
    profpic = models.ImageField(null=True, blank=True, upload_to="headshots")
    imported = models.BooleanField(default=False, editable=False)

    # for photos that previously ran with a photographer_id of 1 and a "courtesy of" caption
    courtesyof = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def works(self):
        return list(chain(
            self.text_set.all(),
            self.video_set.all(),
            self.pdf_set.all(),
            self.photo_set.all(),
            self.html_set.all(),
            self.pullquote_set.all()
        ))

    def published_works(self):
        # Only return works that are published in at least one place
        return [work for work in self.works() if True in [post.is_published for post in work.post_set.all()]]

    def posts(self):
        posts = []
        for work in self.works():
            for post in work.post_set.all():
                posts.append(post)

        return list(set(posts))

    def primary_section(self):
        try:
            section_mapping = [post.section.classname() for post in self.posts()]
            return section_mapping[0]
        except:
            return ""


""" The following models describe things a post can contain.
This is a limited subset for the time being and will expand.
"""


class Text (models.Model):
    class Meta:
        verbose_name_plural = "Text"

    body = models.TextField()
    excerpt = models.TextField(editable=False, null=True)
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.excerpt

    def save(self, *args, **kwargs):
        # Using NLTK here is a sledgehammer for a thumbtack, but it may be useful for tagging, too
        try:
            tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        except:
            print("Error initializing NLTK. Try running 'python manage.py nltk-init'")
        self.excerpt = ' '.join(tokenizer.tokenize(self.body)[:3])
        super(Text, self).save(*args, **kwargs)


class Video(models.Model):
    hosts = (
        ("YouTube", "YouTube"),
        ("Vimeo", "Vimeo"),
        ("Vine", "Vine"),
    )  # the syntax of how you have to do this is really annoying

    host = models.CharField(max_length=7, choices=hosts, default="Vimeo")
    uid = models.CharField(
        max_length=20,
        verbose_name="Video identifier - typically a string of letters or numbers after the last slash in the URL"
    )
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    def url(self):
        return "http://{host}.com/{uid}".format(host=self.host.lower(), uid=self.uid)

    def __str__(self):
        return self.url()


class PDF (models.Model):
    staticfile = models.FileField(upload_to="pdfs")
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.caption[:60]


class Photo (models.Model):
    staticfile = models.ImageField(upload_to="photos")
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    """ get_or_create a thumbnail of the specified width and height """
    def thumbnail(self, width, height):
        pass

    def __str__(self):
        return self.caption[:60]


class HTML (models.Model):
    class Meta:
        verbose_name = "HTML"
        verbose_name_plural = "HTML"

    content = models.TextField()
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        if self.caption:
            return self.caption[:60]
        else:
            return self.content[:60]


class Pullquote (models.Model):
    quote = models.TextField()
    attribution = models.TextField(null=True, blank=True)
    creators = models.ManyToManyField(Creator)
    caption = models.TextField(null=True, blank=True)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.quote


""" The following model describes things a post on the website is.
Posts are most commonly articles, but that terminology is limiting;
a post might be a stand-alone photo or an entry in a video series.

Posts have a ManyToManyField for every type of content
Bongo supports storing for maximum content reusability.
They also have a primary_type, which will help the frontend decide the
layout for that post (a standard article, liveblog, a photo gallery, etc.)
"""


class Post (models.Model):
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    published = models.DateTimeField()
    is_published = models.BooleanField(default=False)  # allow for drafts

    series = models.ManyToManyField(Series, blank=True)
    issue = models.ForeignKey(Issue, null=True, blank=True)  # issue might be null in the case of a web-only post
    volume = models.ForeignKey(Volume)  # volume cannot be null because it represents an academic year
    section = models.ForeignKey(Section)

    title = models.CharField(max_length=180)
    slug = models.CharField(
        max_length=180,
        db_index=True
    )  # http://en.wikipedia.org/wiki/Clean_URL#Slug
    tags = models.ManyToManyField(Tag, blank=True)

    opinion = models.BooleanField(default=False)

    views_local = models.IntegerField(editable=False, default=0)
    views_global = models.IntegerField(editable=False, default=0)

    text = models.ManyToManyField(Text, blank=True)
    video = models.ManyToManyField(Video, blank=True)
    pdf = models.ManyToManyField(PDF, blank=True)
    photo = models.ManyToManyField(Photo, blank=True)
    html = models.ManyToManyField(HTML, blank=True)
    pullquote = models.ManyToManyField(Pullquote, blank=True)

    imported = models.BooleanField(default=False, editable=False)

    types = (
        ("text", "Article"),
        ("photo", "Photo(s)"),
        ("video", "Video(s)"),
        ("liveblog", "Liveblog"),
        ("html", "Interactive/Embedded"),
        ("generic", "Other")
    )

    primary_type = models.CharField(max_length=8, choices=types, default="generic")

    def excerpt(self):
        try:
            ex = ""
            if self.primary_type == "photo":
                ex = self.photo.all()[0].caption
            elif self.primary_type == "video":
                ex = self.video.all()[0].caption
            elif self.primary_type == "html":
                ex = self.HTML.all()[0].caption
            elif self.primary_type == "photo":
                ex = self.photo.all()[0].caption
            elif self.primary_type == "text":
                ex = self.text.all()[0].excerpt
            return strip_tags(ex)
        except:
            logger.error("Could not get an excerpt for article {}".format(self.pk))
            return ""

    def primary_section(self):
        # exists for consistency with other searchable models
        return self.section.classname()

    def content_as_chain(self):
        return chain(
            self.text.all(),
            self.video.all(),
            self.pdf.all(),
            self.photo.all(),
            self.html.all(),
            self.pullquote.all()
        )

    def content_as_text(self):
        content = []

        content.append([item.caption for item in self.photo.all()])
        content.append([item.caption for item in self.video.all()])
        content.append([item.caption for item in self.html.all()])
        content.append([item.caption for item in self.photo.all()])
        content.append([item.body for item in self.text.all()])
        content.append([item.caption for item in self.pullquote.all()])
        content.append([item.quote for item in self.pullquote.all()])

        content = [val for sublist in content for val in sublist if val is not None]

        return ' '.join(content)

    def creators(self):
        crtrs = ()
        for cont in self.content_as_chain():
            crtrs = chain(crtrs, cont.creators.all())
        return set(crtrs)

    def similar_tags(self):
        similarity = {}
        for tag in self.tags.all():
            for similar_post in tag.post_set.all():
                if not similar_post.__eq__(self):
                    if similar_post in similarity:
                        similarity[similar_post] += 1
                    else:
                        similarity[similar_post] = 1

        return [post for (post, count) in sorted(similarity.items(), key=operator.itemgetter(1))]

    def taggit(self):
        if self.text.all():
            for t in tagify(self.text.all()[0].body):
                (tag, created) = Tag.objects.get_or_create(tag=t)
                self.tags.add(tag)
                self.save()

    def popularity(self):
        cache_key = "popularity_{}".format(self.pk)
        cached = cache.get(cache_key)

        if cached:
            return cached
        else:
            current_withtz = make_aware(datetime.now(), tz)
            published_withtz = self.published
            popularity = self.views_global - ((current_withtz - published_withtz).total_seconds() / 10**4.5)

            url = "http://bowdoinorient.com/article/{}".format(self.pk)

            # # get twitter shares
            # try:
            #     res = requests.get("http://urls.api.twitter.com/1/urls/count.json", params={"url":url})
            #     if res.status_code == 200:
            #         popularity = popularity + res.json()['count'] * 7.5
            # except Exception as e:
            #     print(e)

            # # get facebook interactions
            # try:
            #     res = requests.post(
            #         "https://api.facebook.com/restserver.php",
            #         data=json.dumps({
            #             "method": "links.getStats",
            #             "format": "json",
            #             "urls": url
            #         }), headers={
            #             "content-type": "application/json"
            #         })
            #     if res.status_code == 200:
            #         popularity = popularity + res.json()[0]['total_count'] * 5
            # except Exception as e:
            #     print(e)

            cache.set(cache_key, popularity, 7200)

            return popularity

    def save(self, *args, **kwargs):
        auto_dates = kwargs.pop('auto_dates', True)

        if not self.slug:
            newslug = slugify(self.title)[:175]

            # make sure this slug has not been used before
            variant = 2
            while len(Post.objects.filter(slug__exact=newslug)) > 0:
                slug_salt = "-" + str(variant)

                if variant > 2:
                    newslug = newslug[:-len(slug_salt)]

                newslug += slug_salt
                variant += 1

            self.slug = newslug

        # generally we want created to update to the time whenever we create the obj
        # and updated to update every time
        # but during import, we want to use old dates and don't want to overwrite them
        if auto_dates:
            if not self.created:
                self.created = make_aware(datetime.now(), tz)
            self.updated = make_aware(datetime.now(), tz)

        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


""" Other miscellaneous tools """


class Alert (models.Model):
    run_from = models.DateTimeField()
    run_through = models.DateTimeField()
    message = models.TextField()
    urgent = models.BooleanField(default=False)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.message


class Advertiser (models.Model):
    name = models.CharField(max_length=100)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.name


class Ad (models.Model):
    run_from = models.DateField()
    run_through = models.DateField()

    owner = models.ForeignKey(Advertiser)
    url = models.URLField(null=True, blank=True)
    adfile = models.ImageField(upload_to="ads")
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.owner + ": {} through {}".format(self.run_from.strftime("%x"), self.run_through.strftime("%x"))


class Tip (models.Model):
    content = models.TextField()
    respond_to = models.EmailField(null=True, blank=True)
    submitted_at = models.DateTimeField()
    submitted_from = models.GenericIPAddressField(null=True, blank=False)
    useragent = models.TextField(null=True, blank=False)
    imported = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.content[:60]


class Event (models.Model):
    """For our Plancast replacement"""

    imported = models.BooleanField(default=False, editable=False)


class ScheduledPost(models.Model):
    """For our Buffer replacement"""

    imported = models.BooleanField(default=False, editable=False)

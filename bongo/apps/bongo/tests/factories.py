import factory
from bongo.apps.bongo import models
from django.contrib.auth.models import User
from random import choice, sample
from string import lowercase, digits, capitalize, lowercase

class UserFactory(factory.Factory):
    class Meta:
        model = User

    first_name = capitalize(''.join(choice(lowercase) for i in range(6)))
    last_name = capitalize(''.join(choice(lowercase) for i in range(7)))
    username = factory.LazyAttribute(lambda obj: obj.first_name[0] + obj.last_name)
    email = factory.LazyAttribute(lambda obj: obj.username + "@bowdoin.edu")
    password = factory.PostGenerationMethodCall('set_password',
                                                'defaultpassword')


class JobFactory(factory.Factory):
    class Meta:
        model = models.Job

    title = choice(["Editor in Chief", "Opinion Editor", "Contributor", "Staff Writer", "Columnist"])

class CreatorFactory(factory.Factory):
    class Meta:
        model = models.Creator

    user = factory.SubFactory(UserFactory)
    name = capitalize(''.join(choice(lowercase) for i in range(6)))
    job = factory.SubFactory(JobFactory)
    twitter = "@"+''.join(choice(lowercase) for i in range(8))

class ContentFactory(factory.Factory):
    class Meta:
        model = models.Content

    caption = factory.Sequence(lambda n: 'This is content #{0}'.format(n))

class TextFactory(factory.Factory):
    class Meta:
        model = models.Text

    caption = factory.Sequence(lambda n: 'This is text #{0}'.format(n))
    body = "It has a loooooooooooooong body"
    excerpt = "The excerpt isn't correct until it's saved"

class VideoFactory(factory.Factory):
    class Meta:
        model = models.Video

    caption = factory.Sequence(lambda n: 'This is video #{0}'.format(n))
    host = choice(["Vimeo", "YouTube", "Vine"])
    uid = ''.join(choice(lowercase + digits) for i in range(15))

class PDFFactory(factory.Factory):
    class Meta:
        model = models.PDF

    caption = factory.Sequence(lambda n: 'This is pdf #{0}'.format(n))

class PhotoFactory(factory.Factory):
    class Meta:
        model = models.Photo

    caption = factory.Sequence(lambda n: 'This is photo #{0}'.format(n))

class HTMLFactory(factory.Factory):
    class Meta:
        model = models.HTML

    caption = factory.Sequence(lambda n: 'This is html #{0}'.format(n))
    content = "<h1>wooo html</h1>"

class PullquoteFactory(factory.Factory):
    class Meta:
        model = models.Pullquote

    caption = factory.Sequence(lambda n: 'This is pullquote #{0}'.format(n))
    quote = "Success is my only motherfuckin' option, failure's not"
    attribution = "Marshall Mathers, TDD evangelist"
from factories import *
from django.test import TestCase
from django.db import models

class ContentTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()

        # Content doesn't have a defined superclass, is a Content
        self.assertEqual(content.__class__.__name__, "Content")

    def test_fields(self):
        content = ContentFactory.build()
        self.assertIsNotNone(content.caption)


class TextTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        text = TextFactory.build()
        self.assertTrue(issubclass(type(text), type(content)))

    def test_fields(self):
        text = TextFactory.build()
        self.assertIsNotNone(text.caption)

    def test_excerpt(self):
        text = TextFactory.build()
        self.assertEquals(text.excerpt, "The excerpt isn't correct until it's saved")
        text.body = "Quinoa hashtag Kickstarter bespoke. Schlitz PBR&B 3 wolf moon, photo booth swag occupy banh mi PBR artisan lo-fi normcore. Lomo selvage leggings quinoa, ugh cliche cornhole asymmetrical gluten-free Echo Park. Tumblr put a bird on it drinking vinegar sriracha, leggings mumblecore actually four loko twee fixie mustache. Mustache drinking vinegar cliche, meggings before they sold out fap Kickstarter tofu banjo master cleanse ennui fingerstache kogi you probably haven't heard of them. Polaroid photo booth chia biodiesel trust fund typewriter locavore, Blue Bottle 90's Neutra umami flannel. Portland Helvetica umami freegan locavore direct trade, polaroid 3 wolf moon actually."
        text.save()
        self.assertEquals(text.excerpt, "Quinoa hashtag Kickstarter bespoke. Schlitz PBR&B 3 wolf moon, photo booth swag occupy banh mi PBR artisan lo-fi normcore. Lomo selvage leggings quinoa, ugh cliche cornhole asymmetrical gluten-free Echo Park.")
        text.delete()

class VideoTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        video = VideoFactory.build()
        self.assertTrue(issubclass(type(video), type(content)))

    def test_fields(self):
        video = VideoFactory.build()
        self.assertIsNotNone(video.caption)
        self.assertIsNotNone(video.url())


class PDFTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        pdf = PDFFactory.build()
        self.assertTrue(issubclass(type(pdf), type(content)))

    def test_fields(self):
        pdf = PDFFactory.build()
        self.assertIsNotNone(pdf.caption)


class PhotoTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        photo = PhotoFactory.build()
        self.assertTrue(issubclass(type(photo), type(content)))

    def test_fields(self):
        photo = PhotoFactory.build()
        self.assertIsNotNone(photo.caption)


class HTMLTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        html = HTMLFactory.build()
        self.assertTrue(issubclass(type(html), type(content)))

    def test_fields(self):
        html = HTMLFactory.build()
        self.assertIsNotNone(html.caption)
        self.assertIsNotNone(html.content)


class PullquoteTestCase(TestCase):
    def test_inheritance(self):
        content = ContentFactory.build()
        pullquote = PullquoteFactory.build()
        self.assertTrue(issubclass(type(pullquote), type(content)))

    def test_fields(self):
        pullquote = PullquoteFactory.build()
        self.assertIsNotNone(pullquote.caption)
        self.assertIsNotNone(pullquote.quote)
        self.assertIsNotNone(pullquote.attribution)


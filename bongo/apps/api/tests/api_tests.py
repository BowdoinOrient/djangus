from bongo.apps.bongo import models
from bongo.apps.bongo.tests import factories
from bongo.apps.bongo.helpers import arbitrary_serialize
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from .test_helpers import crud
from haystack.management.commands import update_index
from datetime import datetime, timedelta
import json

# @TODO: These tests don't do a very good job of cleaning up after themselves

APIVER = settings.REST_FRAMEWORK['DEFAULT_VERSION']


class APITestCase(TestCase):
    def test_Job_endpoint(self):
        obj = factories.JobFactory.create()
        crud(self, obj, models.Job)

    def test_Creator_endpoint(self):
        obj = factories.CreatorFactory.create()
        crud(self, obj, models.Creator)

    def test_Text_endpoint(self):
        obj = factories.TextFactory.create()
        crud(self, obj, models.Text)

    def test_Video_endpoint(self):
        obj = factories.VideoFactory.create()
        crud(self, obj, models.Video)

    def test_HTML_endpoint(self):
        obj = factories.HTMLFactory.create()
        crud(self, obj, models.HTML)

    def test_Photo_endpoint(self):
        obj = factories.PhotoFactory.create()
        crud(self, obj, models.Photo)

    def test_PDF_endpoint(self):
        obj = factories.PDFFactory.create()
        crud(self, obj, models.PDF)

    def test_Pullquote_endpoint(self):
        obj = factories.PullquoteFactory.create()
        crud(self, obj, models.Pullquote)

    def test_Series_endpoint(self):
        obj = factories.SeriesFactory.create()
        crud(self, obj, models.Series)

    def test_Volume_endpoint(self):
        obj = factories.VolumeFactory.create()
        crud(self, obj, models.Volume)

    def test_Issue_endpoint(self):
        obj = factories.IssueFactory.create()
        crud(self, obj, models.Issue)

    def test_Tag_endpoint(self):
        obj = factories.TagFactory.create()
        crud(self, obj, models.Tag)

    def test_Post_endpoint(self):
        obj = factories.PostFactory.create()
        crud(self, obj, models.Post)

    def test_Section_endpoint(self):
        obj = factories.SectionFactory.create()
        crud(self, obj, models.Section)

    def test_Section_Post_endpoint(self):
        """Test Section's additional @list_route, /section/<id>/posts/"""
        client = APIClient()

        section = factories.SectionFactory.create()

        posts = [factories.PostFactory.create() for x in range(3)]

        for post in posts:
            post.section = section
            post.published = datetime.now() + timedelta(hours=post.pk)
            post.save(auto_dates=False)

        res = client.get("http://testserver/api/{v}/section/{pk}/posts/".format(v=APIVER, pk=section.pk))

        self.assertEqual(res.status_code, 200)

        js_res = json.loads(res.content.decode("utf-8"))

        self.assertEqual([p['id'] for p in js_res["posts"]], [p.id for p in reversed(posts)])

        # Test with pagination

        res = client.get("http://testserver/api/{v}/section/{pk}/posts/?limit=2".format(v=APIVER, pk=section.pk))

        self.assertEqual(res.status_code, 200)

        js_res = json.loads(res.content.decode("utf-8"))

        self.assertEqual(len(js_res['posts']), 2)

        # Test ordering

        res = client.get("http://testserver/api/{v}/section/{pk}/posts/?ordering=published".format(
            v=APIVER,
            pk=section.pk
        ))

        self.assertEqual(res.status_code, 200)

        js_res = json.loads(res.content.decode("utf-8"))

        self.assertEqual([p['id'] for p in js_res["posts"]], [p.id for p in posts])

    def test_root_endpoint(self):
        client = APIClient()

        res = client.get("http://testserver/api/{v}/".format(v=APIVER))

        self.assertEqual(res.status_code, 200)

        js_res = json.loads(res.content.decode("utf-8"))

        js_res_keys = js_res.keys()

        for model in [
            "series", "volume", "issue", "section", "tag", "job", "creator", "text", "video", "pdf", "photo", "html",
            "pullquote", "post", "alert", "advertiser", "ad", "tip", "event", "scheduledpost", "search"
        ]:
            self.assertIn(model, js_res_keys)

        for model in js_res_keys:
            res = client.get(js_res[model])

            # Some endpoints do not accept GET, so allow a 405 status code
            self.assertIn(res.status_code, [200, 405])

    def test_search_endpoint(self):
        client = APIClient()

        creator = factories.CreatorFactory.create()

        update_index.Command().handle(using=['default'], age=1, verbosity=0, interactive=False)

        res = client.post("http://testserver/api/{v}/search/".format(v=APIVER), {
            "query": creator.name
        })

        self.assertEqual(res.status_code, 200)

        js_res = json.loads(res.content.decode("utf-8"))

        self.assertIn(arbitrary_serialize(creator), js_res)

    def test_pagination(self):
        issue1 = factories.IssueFactory.create()
        issue2 = factories.IssueFactory.create()

        client = APIClient()

        res = client.get("http://testserver/api/{v}/issue/?limit=1".format(v=APIVER))
        js = json.loads(res.content.decode("utf-8"))

        self.assertEqual(len(js['results']), 1)
        self.assertEqual(js['results'][0]['id'], issue1.pk)

        res = client.get(js['next'])
        js = json.loads(res.content.decode("utf-8"))
        self.assertEqual(js['results'][0]['id'], issue2.pk)
        self.assertEqual(js['next'], None)

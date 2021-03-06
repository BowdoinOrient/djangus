from django.test import TestCase
from bongo.apps.bongo.models import Creator, Series, Post
from bongo.apps.bongo.tests.factories import CreatorFactory, SeriesFactory, PostFactory
from haystack.query import SearchQuerySet
from haystack.management.commands import update_index
from django.core import urlresolvers


class SearchTestCase(TestCase):
    def test_creator_search(self):
        """Assert that you can find Creators via search"""

        obj = CreatorFactory.create()

        update_index.Command().handle(using=['default'], age=1, verbosity=0, interactive=False)

        sqs = SearchQuerySet().all()

        res = sqs.auto_query(obj.name)

        self.assertGreater(len(res), 0)
        self.assertIn(Creator.objects.filter(pk__exact=obj.pk).first(), [res_item.object for res_item in res])

    def test_series_search(self):
        """Assert that you can find Series via search"""

        obj = SeriesFactory.create()

        update_index.Command().handle(using=['default'], age=1, verbosity=0, interactive=False)

        sqs = SearchQuerySet().all()

        res = sqs.auto_query(obj.name)

        self.assertGreater(len(res), 0)
        self.assertIn(Series.objects.filter(pk__exact=obj.pk).first(), [res_item.object for res_item in res])

    def test_article_search(self):
        """Assert that you can find Articles via search"""

        obj = PostFactory.create()
        obj.is_published = True
        obj.save()

        update_index.Command().handle(using=['default'], age=1, verbosity=0, interactive=False)

        sqs = SearchQuerySet().all()

        # Haystack seems to only be returning searches for complete words
        # So some finangling here is needed until I figure that out
        res = sqs.auto_query(obj.text.all()[0].body.split(' ')[0])

        self.assertGreater(len(res), 0)
        self.assertIn(Post.objects.get(pk__exact=obj.pk), [res_item.object for res_item in res])

    def test_search_view(self):
        """Test that you can search by querying the search page"""

        obj = CreatorFactory.create()
        update_index.Command().handle(using=['default'], age=1, verbosity=0, interactive=False)

        res = self.client.get(urlresolvers.reverse("haystack_search"), {"q": obj.name})

        self.assertGreater(len(res.context['page'].object_list), 0)
        self.assertEqual(res.context['page'].object_list[0].object, obj)

# -*- coding: utf-8 -*-:
from django.db import models
from django.db.models import Count
from django.utils.timezone import utc
from datetime import timedelta, datetime
from django.contrib.auth.models import User


class VoteManager(models.Manager):

    def my_upvoted_links(self, user):
        qs = self.get_query_set() \
            .filter(user=user)
        qs = qs \
            .exclude(link=None) \
            .values('link__pk', 'link__slug', 'link__title') \
            .annotate(count=Count('id')) \
            .order_by('-time')
        return qs


    def my_upvoted_lists(self, user):
        return self.get_query_set() \
            .exclude(alist=None) \
            .filter(user=user) \
            .values('alist__pk', 'alist__slug', 'alist__title') \
            .annotate(count=Count('id')) \
            .order_by('-time')


    def hottest_links(self, limit=10, days=1, lang_filter=[1]):
        from resrc.link.models import Link
        qs = self.get_query_set() \
            .filter(time__gt=datetime.utcnow().replace(tzinfo=utc) - timedelta(days=days))
        if lang_filter:
            qs = qs.filter(link__language__in=lang_filter)
        qs = qs \
            .exclude(link=None) \
            .values_list('link__pk', flat=True)
        qs = qs

        qs = self.get_query_set() \
            .filter(link__pk__in=qs) \
            .values('link__pk', 'link__slug', 'link__title') \
            .annotate(count=Count('id')) \
            .order_by('-count')

        for link in qs:
            link['tags'] = Link.objects.filter(pk=link['link__pk']).select_related('tags').values_list('tags__slug', 'tags__name')
        return qs[:limit]


    def latest_links(self, limit=10, days=1, lang_filter=[1]):
        from resrc.link.models import Link
        latest = list(Link.objects.latest(limit=limit, lang_filter=lang_filter))
        voted = self.get_query_set() \
            .filter(time__gt=datetime.utcnow().replace(tzinfo=utc) - timedelta(days=days)) \
            .exclude(link=None) \
            .filter(link__language__in=lang_filter) \
            .values('link__pk', 'link__slug', 'link__title') \
            .annotate(count=Count('id')) \
            .order_by('-link__pubdate')[:limit]
        voted = list(voted)

        voted_id = [link['link__pk'] for link in voted]

        links = []
        for link in latest:
            if link['pk'] in voted_id:
                new_link = [l for l in voted if l['link__pk'] == link['pk']]
                links += new_link
            else:
                new_link = {}
                new_link['count'] = 0
                new_link['link__pk'] = link['pk']
                new_link['link__slug'] = link['slug']
                new_link['link__title'] = link['title']
                links += [new_link]
        return links[:limit]


    def hottest_lists(self, limit=10, days=1, lang_filter=[1]):  # TODO: implement lang filter
        qs = self.get_query_set() \
            .filter(time__gt=datetime.utcnow().replace(tzinfo=utc) - timedelta(days=days)) \
            .exclude(alist=None) \
            .exclude(alist__is_public=False) \
            .values_list('alist__pk', flat=True)
        qs = qs

        qs = self.get_query_set() \
            .filter(alist__pk__in=qs) \
            .values('alist__pk', 'alist__slug', 'alist__title') \
            .annotate(count=Count('id')) \
            .order_by('-count')
        return qs[:limit]


    def votes_for_link(self, link_pk):
        return len(list(self.get_query_set() \
            .filter(link__pk=link_pk)))


    def votes_for_list(self, list_pk):
        return len(list(self.get_query_set() \
            .filter(alist__pk=list_pk)))


class Vote(models.Model):

    objects = VoteManager()

    user = models.ForeignKey(User, verbose_name='user')
    alist = models.ForeignKey('list.List', null=True, blank=True)
    link = models.ForeignKey('link.Link', null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)

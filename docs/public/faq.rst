##################
Frequent Questions
##################

.. contents::
    :depth: 1
    :local:

.. _localemiddleware:

*************************************************
How do I get the right language from the request?
*************************************************

In most cases, you will be using :ref:`language() <language-public>` with no
arguments in your views and forms. When used with no arguments, it defaults
to using the current language, as returned by Django's
:func:`~django.utils.translation.get_language`.

Therefore, having hvad use the right language is mostly a matter of having
Django setting it right. Fortunately, Django provide the tools to do this,
in the form of the :class:`~django.middleware.locale.LocaleMiddleware`. Here is
a short guide to making it work.

First, the middleware must be enabled. This is done by adding
``'django.middleware.locale.LocaleMiddleware'`` to :setting:`MIDDLEWARE_CLASSES`
in you settings file.

- It must come after :class:`~django.contrib.sessions.middleware.SessionMiddleware`.
- If you use the ``CacheMiddleware``, then the ``LocaleMiddleware`` must come after
  that too.
- Right after those, as close to the top as possible, should the ``LocaleMiddleware``
  come::

    MIDDLEWARE_CLASSES = (
        'django.middleware.cache.UpdateCacheMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
    )

Now, the middleware will try to determine the user's language preference. There is
a detailed explanation of how it proceeds in
:djterm:`Django documentation <how-django-discovers-language-preference>`.

Hvad will happily follow the language discovered by the middleware. Although this
will usually be enough, you may sometimes want to force the language. Either
on a specific request by explicitly passing a language code to
:ref:`language() <language-public>`, or by changing the current language. The
later is done through :func:`~django.utils.translation.activate`.


***************************
How about multilingual URI?
***************************

We will assume the URI we want to be multilingual are made of two kind of components:
static components, and dynamic components. We want to translate both kind:

- Static components, through :func:`~django.utils.translation.ugettext_lazy`.
- Dynamic components, from our translatable models.

Static components
=================

This is thoroughly documented in Django's
:djterm:`URL i18n documentation <url-internationalization>` and does not actually
involve hvad, so this will be a short guide. It requires the
:class:`~django.middleware.locale.LocaleMiddleware` to be properly
:ref:`configured <localemiddleware>`, so please do that first.

With this middleware active, each request will set a current language before
looking up the URI in your ``urlconf.py``. This makes it possible to use
:func:`~django.utils.translation.ugettext_lazy` in your patterns, like this::

    from django.conf.urls import url
    from django.utils.translation import ugettext_lazy as _

    urlpatterns = [
        url(_(r'^en/news/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<slug>.*)'),
            views.NewsView, name='news-detail'),
    ]

The pattern would then appear in the list of translatable string, making it
possible to add, for instance, a translation that would read
``^fr/actualites/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<slug>.*)``

.. note:: Notice the language code at the beginning. Although not required,
          prefixing your URI with it makes the life much easier to the
          :class:`~django.middleware.locale.LocaleMiddleware`.

Dynamic components
==================

We translated the static parts of the URI with Django mechanics. What now?
Well, if we touch nothing, everything will work fine: the language of the user
will be used for URI resolution, and then hvad's :ref:`language() <language-public>`
will follow the same. Database queries will filter on the user's language
by default, and your view will 404 if nothing is found in that language.

Now, in some instances, the language might not be known. Because your URI does
not include a language code, or because you want to find objects regardless
of the user's language. Maybe based on a translatable slug. This can be done
by querying with ``language('all')``::

    from django.views.generic.base import TemplateView

    class NewsView(TemplateView):
        def get(self, request, *args, **kwargs):
            slug = kwargs['slug']
            obj = News.objects.language('all').get(published=True, slug=slug)

            context = self.get_context_data(news=obj, language=obj.language_code)
            return self.render_to_response(context)

This view will find the news given its slug, regardless of which language it
is in. It will display it in the language it is found with. It would be possible
to force it to be in the user's preferred language by adding another query::

    obj = News.objects.language('all').get(published=True, slug=slug)
    try:
        # Try to replace obj with a version in current user's language
        obj = News.objects.language().get(pk=obj.pk)
    except News.DoesNotExist:
        # No translation for user's language, stick with that of the slug
        pass

.. note:: Note those examples assume slugs are unique amongst all news of all
          languages.


****************************
How do I use hvad with MPTT?
****************************

The `mptt`_ application implements Modified Preorder Tree Traversal
for Django models. If you have any model in your project that is organized
in a hierarchy of items, you should be using it.

However, this code will break mysteriously if you are not familiar with python
metaclasses::

    class Folder(MPTTModel, TranslatableModel):
        parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
        order = models.PositiveIntegerField()
        translations = TranslatedFields(
            name = models.CharField(max_length=50)
        )

        class MPTTMeta:
            order_insertion_by = ['order']

This will result in the following exception being thrown::

    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    TypeError: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases

This is because both `MPTTModel` and :class:`~hvad.models.TranslatableModel`
use metaclasses and Python is confused: which should it use for the Folder model?
We need to create one by ourselves, like this::

    class FolderBase(TranslatableModel.__class__, MPTTModel.__class__):
        pass

    class Folder(MPTTModel, TranslatableModel):
        __metaclass__ = FolderBase
        # ...

.. note:: If you have multiple levels of inheritance, you have to specify the
          metaclass for each class.

While you are there, it is very likely you will want to use the features of
the MPTT manager as well. Doing so is relatively straightforward::

    class FolderManager(TranslationManager, MPTTManager):
        use_for_related_fields = True

    class Folder(MPTTModel, TranslatableModel):
        # ...
        objects = FolderManager()

The same principle would work with a custom queryset too, but MPTT does not
define one.


.. _mptt: https://github.com/django-mptt/django-mptt/


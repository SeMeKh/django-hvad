# -*- coding: utf-8 -*-
from __future__ import with_statement
import django
from django.core.exceptions import ImproperlyConfigured
from django.db.models.manager import Manager
from django.db.models.query_utils import Q
from hvad.manager import TranslationManager
from hvad.models import TranslatableModelBase, TranslatableModel
from hvad.test_utils.context_managers import LanguageOverride
from hvad.test_utils.data import DOUBLE_NORMAL
from hvad.test_utils.fixtures import (OneSingleTranslatedNormalMixin, 
    TwoTranslatedNormalMixin)
from hvad.test_utils.testcase import HvadTestCase, minimumDjangoVersion
from hvad.test_utils.project.app.models import Normal, MultipleFields, Boolean
from hvad.test_utils.project.alternate_models_app.models import NormalAlternate


class InvalidModel2(object):
    objects = TranslationManager()


class DefinitionTests(HvadTestCase):
    def test_invalid_manager(self):
        attrs = {
            'objects': Manager(),
            '__module__': 'hvad.test_utils.project.app',
        }
        self.assertRaises(ImproperlyConfigured, TranslatableModelBase,
                          'InvalidModel', (TranslatableModel,), attrs)
    
    def test_no_translated_fields(self):
        attrs = dict(InvalidModel2.__dict__)
        del attrs['__dict__']
        del attrs['__weakref__']
        bases = (TranslatableModel,InvalidModel2,)
        self.assertRaises(ImproperlyConfigured, TranslatableModelBase,
                          'InvalidModel2', bases, attrs)
    
    def test_abstract_base_model(self):
        class Meta:
            abstract = True
        attrs = {
            'Meta': Meta,
            '__module__': 'hvad.test_utils.project.app',
        }
        model = TranslatableModelBase('MyBaseModel', (TranslatableModel,), attrs)
        self.assertTrue(model._meta.abstract)


class OptionsTest(HvadTestCase):
    def test_options(self):
        opts = Normal._meta
        self.assertTrue(hasattr(opts, 'translations_model'))
        self.assertTrue(hasattr(opts, 'translations_accessor'))
        relmodel = Normal._meta.get_field_by_name(opts.translations_accessor)[0].model
        self.assertEqual(relmodel, opts.translations_model)


class AlternateCreateTest(HvadTestCase):
    def test_create_instance_simple(self):
        obj = NormalAlternate(language_code='en')
        obj.shared_field = "shared"
        obj.translated_field = "English"
        obj.save()
        en = NormalAlternate.objects.language('en').get(pk=obj.pk)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
    

class CreateTest(HvadTestCase):
    def test_create(self):
        with self.assertNumQueries(2):
            en = Normal.objects.language('en').create(
                shared_field="shared",
                translated_field='English',
            )
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
    
    def test_invalid_instantiation(self):
        self.assertRaises(RuntimeError, Normal, master=None)
    
    def test_create_nolang(self):
        with self.assertNumQueries(2):
            with LanguageOverride('en'):
                en = Normal.objects.create(
                    shared_field="shared",
                    translated_field='English',
                )
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
    
    def test_create_instance_simple(self):
        obj = Normal(language_code='en')
        obj.shared_field = "shared"
        obj.translated_field = "English"
        obj.save()
        en = Normal.objects.language('en').get(pk=obj.pk)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
        
    def test_create_instance_shared(self):
        obj = Normal(language_code='en', shared_field = "shared")
        obj.save()
        en = Normal.objects.language('en').get(pk=obj.pk)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.language_code, "en")
        
    def test_create_instance_translated(self):
        obj = Normal(language_code='en', translated_field = "English")
        obj.save()
        en = Normal.objects.language('en').get(pk=obj.pk)
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
    
    def test_create_instance_both(self):
        obj = Normal(language_code='en', shared_field = "shared",
                     translated_field = "English")
        obj.save()
        en = Normal.objects.language('en').get(pk=obj.pk)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")
        
    def test_create_instance_simple_nolang(self):
        with LanguageOverride('en'):
            obj = Normal(language_code='en')
            obj.shared_field = "shared"
            obj.translated_field = "English"
            obj.save()
            en = Normal.objects.language('en').get(pk=obj.pk)
            self.assertEqual(en.shared_field, "shared")
            self.assertEqual(en.translated_field, "English")
            self.assertEqual(en.language_code, "en")
        
    def test_create_instance_shared_nolang(self):
        with LanguageOverride('en'):
            obj = Normal(language_code='en', shared_field = "shared")
            obj.save()
            en = Normal.objects.language('en').get(pk=obj.pk)
            self.assertEqual(en.shared_field, "shared")
            self.assertEqual(en.language_code, "en")
        
    def test_create_instance_translated_nolang(self):
        with LanguageOverride('en'):
            obj = Normal(language_code='en', translated_field = "English")
            obj.save()
            en = Normal.objects.language('en').get(pk=obj.pk)
            self.assertEqual(en.translated_field, "English")
            self.assertEqual(en.language_code, "en")
    
    def test_create_instance_both_nolang(self):
        with LanguageOverride('en'):
            obj = Normal(language_code='en', shared_field = "shared",
                         translated_field = "English")
            obj.save()
            en = Normal.objects.language('en').get(pk=obj.pk)
            self.assertEqual(en.shared_field, "shared")
            self.assertEqual(en.translated_field, "English")
            self.assertEqual(en.language_code, "en")

    def test_create_instance_untranslated(self):
        with self.assertNumQueries(1):
            with LanguageOverride('en'):
                ut = Normal.objects.create(
                    shared_field="shared",
                )
        self.assertEqual(ut.shared_field, "shared")
        with self.assertNumQueries(1):
            with self.assertRaises(AttributeError):
                ut.translated_field
        with self.assertNumQueries(1):
            with self.assertRaises(AttributeError):
                ut.language_code


class TranslatedTest(HvadTestCase, OneSingleTranslatedNormalMixin):
    def test_translate(self):
        SHARED_EN = 'shared'
        TRANS_EN = 'English'
        SHARED_JA = 'shared'
        TRANS_JA = u'日本語'
        en = Normal.objects.language('en').get(pk=1)
        self.assertEqual(Normal._meta.translations_model.objects.count(), 1)
        self.assertEqual(en.shared_field, SHARED_EN)
        self.assertEqual(en.translated_field, TRANS_EN)
        ja = en
        ja.translate('ja')
        ja.save()
        self.assertEqual(Normal._meta.translations_model.objects.count(), 2)
        self.assertEqual(ja.shared_field, SHARED_JA)
        self.assertEqual(ja.translated_field, '')
        ja.translated_field = TRANS_JA
        ja.save()
        self.assertEqual(Normal._meta.translations_model.objects.count(), 2)
        self.assertEqual(ja.shared_field, SHARED_JA)
        self.assertEqual(ja.translated_field, TRANS_JA)
        with LanguageOverride('en'):
            obj = self.reload(ja)
            self.assertEqual(obj.shared_field, SHARED_EN)
            self.assertEqual(obj.translated_field, TRANS_EN)
        with LanguageOverride('ja'):
            obj = self.reload(en)
            self.assertEqual(obj.shared_field, SHARED_JA)
            self.assertEqual(obj.translated_field, TRANS_JA)
        

class GetTest(HvadTestCase, OneSingleTranslatedNormalMixin):
    def test_get(self):
        en = Normal.objects.language('en').get(pk=1)
        with self.assertNumQueries(1):
            got = Normal.objects.language('en').get(pk=en.pk)
        with self.assertNumQueries(0):
            self.assertEqual(got.shared_field, "shared")
            self.assertEqual(got.translated_field, "English")
            self.assertEqual(got.language_code, "en")

    def test_filtered_get(self):
        obj = Normal(shared_field='field_1')
        obj.translate('en')
        obj.translated_field = 'field_2'
        obj.save()
        qs = Normal.objects.language('en') | Normal.objects.language('de')
        found = qs.filter(shared_field='field_1').get(pk=obj.pk)
        self.assertEqual(found.pk, obj.pk)
    
    def test_safe_translation_getter(self):
        untranslated = Normal.objects.untranslated().get(pk=1)
        with LanguageOverride('en'):
            self.assertEqual(untranslated.safe_translation_getter('translated_field', None), None)
            Normal.objects.untranslated().get(pk=1)
            self.assertEqual(untranslated.safe_translation_getter('translated_field', "English"), "English")
        with LanguageOverride('ja'):
            self.assertEqual(untranslated.safe_translation_getter('translated_field', None), None)
            self.assertEqual(untranslated.safe_translation_getter('translated_field', "Test"), "Test")
        


class GetByLanguageTest(HvadTestCase, TwoTranslatedNormalMixin):
    
    def test_args(self):
        with LanguageOverride('en'):
            q = Q(language_code='ja', pk=1)
            obj = Normal.objects.using_translations().get(q)
            self.assertEqual(obj.shared_field, DOUBLE_NORMAL[1]['shared_field'])
            self.assertEqual(obj.translated_field, DOUBLE_NORMAL[1]['translated_field_ja'])
    
    def test_kwargs(self):
        with LanguageOverride('en'):
            kwargs = {'language_code':'ja', 'pk':1}
            obj = Normal.objects.using_translations().get(**kwargs)
            self.assertEqual(obj.shared_field, DOUBLE_NORMAL[1]['shared_field'])
            self.assertEqual(obj.translated_field, DOUBLE_NORMAL[1]['translated_field_ja'])
        
    def test_language(self):
        with LanguageOverride('en'):
            obj = Normal.objects.language('ja').get(pk=1)
            self.assertEqual(obj.shared_field, DOUBLE_NORMAL[1]['shared_field'])
            self.assertEqual(obj.translated_field, DOUBLE_NORMAL[1]['translated_field_ja'])


class GetAllLanguagesTest(HvadTestCase, TwoTranslatedNormalMixin):
    def test_args(self):
        with LanguageOverride('en'):
            q = Q(pk=1)
            with self.assertNumQueries(1):
                objs = Normal.objects.language('all').filter(q)
                self.assertEqual(len(objs), 2)
                self.assertCountEqual((1, 1), (objs[0].pk, objs[1].pk))
                self.assertCountEqual(('en', 'ja'), (objs[0].language_code, objs[1].language_code))

    def test_kwargs(self):
        with LanguageOverride('en'):
            kwargs = {'pk':1}
            with self.assertNumQueries(1):
                objs = Normal.objects.language('all').filter(**kwargs)
                self.assertEqual(len(objs), 2)
                self.assertCountEqual((1, 1), (objs[0].pk, objs[1].pk))
                self.assertCountEqual(('en', 'ja'), (objs[0].language_code, objs[1].language_code))

    def test_translated_unique(self):
        with LanguageOverride('en'):
            with self.assertNumQueries(1):
                obj = Normal.objects.language('all').get(translated_field=DOUBLE_NORMAL[1]['translated_field_ja'])
                self.assertEqual(obj.pk, 1)
                self.assertEqual(obj.language_code, 'ja')
                self.assertEqual(obj.shared_field, DOUBLE_NORMAL[1]['shared_field'])
                self.assertEqual(obj.translated_field, DOUBLE_NORMAL[1]['translated_field_ja'])

    def test_get_all_raises(self):
        with self.assertRaises(ValueError):
            Normal.objects.language('en').get(pk=1, language_code='all')


class BasicQueryTest(HvadTestCase, OneSingleTranslatedNormalMixin):
    def test_basic(self):
        en = Normal.objects.language('en').get(pk=1)
        with self.assertNumQueries(1):
            queried = Normal.objects.language('en').get(pk=en.pk)
            self.assertEqual(queried.shared_field, en.shared_field)
            self.assertEqual(queried.translated_field, en.translated_field)
            self.assertEqual(queried.language_code, en.language_code)


class DeleteLanguageCodeTest(HvadTestCase, OneSingleTranslatedNormalMixin):
    def test_delete_language_code(self):
        en = Normal.objects.language('en').get(pk=1)
        self.assertRaises(AttributeError, delattr, en, 'language_code')

                              
class DescriptorTests(HvadTestCase):
    def test_translated_attribute_set(self):
        # 'MyDescriptorTestModel' should return the default field value, in case there is no translation
        from hvad.models import TranslatedFields
        from django.db import models
        
        DEFAULT = 'world'
        class MyDescriptorTestModel(TranslatableModel):
            translations = TranslatedFields(
                hello = models.CharField(default=DEFAULT, max_length=128)
            )
        self.assertEqual(MyDescriptorTestModel.hello, DEFAULT)
    
    def test_translated_attribute_delete(self):    
        # Its not possible to delete the charfield, which should result in an AttributeError
        obj = Normal.objects.language("en").create(shared_field="test", translated_field="en")
        obj.save()
        self.assertEqual(obj.translated_field, "en")
        delattr(obj, 'translated_field')
        self.assertRaises(AttributeError, getattr, obj, 'translated_field')
    
    def test_languagecodeattribute(self):
        # Its not possible to set/delete a language code
        self.assertRaises(AttributeError, setattr, Normal(), 'language_code', "en")
        self.assertRaises(AttributeError, delattr, Normal(), 'language_code')


class TableNameTest(HvadTestCase):
    def test_table_name_separator(self):
        from hvad.models import TranslatedFields
        from django.db import models
        from django.conf import settings
        sep = getattr(settings, 'HVAD_TABLE_NAME_SEPARATOR', '_')
        class MyTableNameTestModel(TranslatableModel):
            translations = TranslatedFields(
                hello = models.CharField(max_length=128)
            )
        self.assertTrue(MyTableNameTestModel.translations.related.model._meta.db_table.endswith('_mytablenametestmodel%stranslation' % sep))

    @minimumDjangoVersion(1, 4)
    def test_table_name_override(self):
        from hvad.models import TranslatedFields
        from django.db import models
        with self.settings(HVAD_TABLE_NAME_SEPARATOR='O_O'):
            class MyOtherTableNameTestModel(TranslatableModel):
                translations = TranslatedFields(
                    hello = models.CharField(max_length=128)
                )
            self.assertTrue(MyOtherTableNameTestModel.translations.related.model._meta.db_table.endswith('_myothertablenametestmodelO_Otranslation'))

    @minimumDjangoVersion(1, 4)
    def test_table_name_override_rename(self):
        with self.assertThrowsWarning(DeprecationWarning, 1):
            with self.settings(NANI_TABLE_NAME_SEPARATOR='O_O'):
                pass

    def test_table_name_from_meta(self):
        from hvad.models import TranslatedFields
        from django.db import models
        class MyTableNameTestNamedModel(TranslatableModel):
            translations = TranslatedFields(
                hello = models.CharField(max_length=128),
                meta = {'db_table': 'tests_mymodel_i18n'},
            )
        self.assertEqual(MyTableNameTestNamedModel.translations.related.model._meta.db_table, 'tests_mymodel_i18n')


class GetOrCreateTest(HvadTestCase):
    def test_create_new_translatable_instance(self):
        with self.assertNumQueries(3 if django.VERSION < (1, 6) else 5):
            """
            1: get
            2a: savepoint (django >= 1.6)
            2b: create shared
            3a: create translation
            3b: release savepoint (django >= 1.6)
            """
            en, created = Normal.objects.language('en').get_or_create(
                shared_field="shared",
                defaults={'translated_field': 'English',},
            )
        self.assertTrue(created)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")

    def test_create_new_language(self):
        en = Normal.objects.language('en').create(
            shared_field="shared",
            translated_field='English',
        )
        with self.assertNumQueries(3 if django.VERSION < (1, 6) else 5):
            """
            1: get
            2a: savepoint (django >= 1.6)
            2b: create shared
            3a: create translation
            3b: release savepoint (django >= 1.6)
            """
            ja, created = Normal.objects.language('ja').get_or_create(
                shared_field="shared",
                defaults={'translated_field': u'日本語',},
            )
        self.assertTrue(created)
        self.assertEqual(ja.shared_field, "shared")
        self.assertEqual(ja.translated_field, u'日本語')
        self.assertEqual(ja.language_code, "ja")
        self.assertNotEqual(en.pk, ja.pk)

    def test_get_existing_language(self):
        Normal.objects.language('en').create(
            shared_field="shared",
            translated_field='English',
        )
        with self.assertNumQueries(1):
            """
            1: get
            """
            en, created = Normal.objects.language('en').get_or_create(
                shared_field="shared",
                defaults={'translated_field': 'x-English',},
            )
        self.assertFalse(created)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")

    # Evil starts here

    def test_split_params(self):
        en, created = Normal.objects.language('en').get_or_create(
            shared_field="shared",
            translated_field="English",
        )
        self.assertTrue(created)
        self.assertEqual(en.shared_field, "shared")
        self.assertEqual(en.translated_field, "English")
        self.assertEqual(en.language_code, "en")

    def test_split_params_shared_already_exists(self):
        Normal.objects.language('en').create(
            shared_field="shared",
            translated_field="English",
        )
        en, created = Normal.objects.language('en').get_or_create(
            shared_field="shared",
            translated_field="x-English"
        )
        self.assertTrue(created)

    def test_new_language_split_params(self):
        en = Normal.objects.language('en').create(
            shared_field="shared",
            translated_field="English",
        )
        ja, created = Normal.objects.language('ja').get_or_create(
            shared_field="shared",
            translated_field=u'日本語',
        )
        self.assertTrue(created)
        self.assertEqual(ja.shared_field, "shared")
        self.assertEqual(ja.translated_field, u'日本語')
        self.assertEqual(ja.language_code, "ja")
        self.assertNotEqual(en.pk, ja.pk)

    def test_split_defaults(self):
        en, created = MultipleFields.objects.language('en').get_or_create(
            first_shared_field="shared-one",
            first_translated_field='English-one',
            defaults={
                'second_shared_field': 'shared-two',
                'second_translated_field': 'English-two',
            }
        )
        self.assertTrue(created)
        self.assertEqual(en.first_shared_field, "shared-one")
        self.assertEqual(en.second_shared_field, "shared-two")
        self.assertEqual(en.first_translated_field, "English-one")
        self.assertEqual(en.second_translated_field, "English-two")
        self.assertEqual(en.language_code, "en")

    def test_new_language_split_defaults(self):
        en = MultipleFields.objects.language('en').create(
            first_shared_field="shared-one",
            second_shared_field='shared-two',
            first_translated_field='English-one',
            second_translated_field='English-two',
        )
        ja, created = MultipleFields.objects.language('ja').get_or_create(
            first_shared_field="shared-one",
            first_translated_field=u'日本語-一',
            defaults={
                'second_shared_field': 'x-shared-two',
                'second_translated_field': u'日本語-二',
            }
        )
        self.assertTrue(created)
        self.assertEqual(ja.first_shared_field, "shared-one")
        #self.assertEqual(ja.second_shared_field, "shared-two")
        self.assertEqual(ja.first_translated_field, u'日本語-一')
        self.assertEqual(ja.second_translated_field,  u'日本語-二')
        self.assertEqual(ja.language_code, "ja")
        self.assertNotEqual(en.pk, ja.pk)


class BooleanTests(HvadTestCase):
    def test_boolean_on_shared(self):
        Boolean.objects.language('en').create(shared_flag=True, translated_flag=False)
        en = Boolean.objects.language('en').get()
        self.assertEqual(en.shared_flag, True)
        self.assertEqual(en.translated_flag, False)

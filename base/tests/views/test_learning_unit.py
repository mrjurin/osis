##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from unittest import mock

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from base.models import learning_unit_component
from base.models import learning_unit_component_class
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_component_class import LearningUnitComponentClassFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.entity_component_year import EntityComponentYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.models.enums import entity_container_year_link_type
from base.tests.factories.user import SuperUserFactory
from base.views import learning_unit as learning_unit_view
from django.utils.translation import ugettext_lazy as _


class LearningUnitViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        self.learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year)
        self.learning_component_yr = LearningComponentYearFactory(learning_container_year=self.learning_container_yr)
        self.entity_container_yr = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                         type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_learning_units(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()

        request = request_factory.get(reverse('learning_units'))
        request.user = mock.Mock()

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['academic_years']), 1)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_learning_units_search(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_units'))
        request.user = mock.Mock()

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['academic_years'].count(), 1)
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['types']),
                         len(learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES))
        self.assertEqual(len(context['container_types']),
                         len(learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES))
        self.assertTrue(context['experimental_phase'])
        self.assertIsNone(context['learning_units'])

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_acronym_filtering(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': True,
            'acronym': 'LBIR'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = mock.Mock()
        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 3)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ENVI'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = mock.Mock()
        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 1)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity_and_subord(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = mock.Mock()
        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 6)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_read(self, mock_program_manager, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        mock_program_manager.return_value = True

        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year)

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit', args=[learning_unit_year.id]))
        request.user = mock.Mock()

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(context['learning_unit_year'], learning_unit_year)

    def test_get_components_no_learning_container_yr(self):
        self.assertEqual(len(learning_unit_view.get_components(None, False)), 0)

    def test_get_components_with_classes(self):
        l_container = LearningContainerFactory()
        l_container_year = LearningContainerYearFactory.build(academic_year=self.current_academic_year,
                                                              title="LC-98998",
                                                              learning_container=l_container)
        l_container_year.save()
        l_component_year = LearningComponentYearFactory(learning_container_year=l_container_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        LearningClassYearFactory(learning_component_year=l_component_year)

        components = learning_unit_view.get_components(l_container_year, True)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0]['learning_component_year'].classes), 2)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_get_partims_identification_tabs(self, mock_program_manager, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        mock_program_manager.return_value = True

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210A",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210B",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210F",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit', args=[learning_unit_year.id]))
        request.user = mock.Mock()

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(len(context['learning_container_year_partims']), 3)

    def test_volumes_undefined(self):
        entity_component_yr = EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                                         entity_container_year=self.entity_container_yr,
                                                         hourly_volume_total=0.00)
        data = learning_unit_view.volumes(entity_component_yr)
        self.assertEqual(data.get(learning_unit_view.HOURLY_VOLUME_KEY), learning_unit_view.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_view.TOTAL_VOLUME_KEY), learning_unit_view.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_view.VOLUME_PARTIAL_KEY), learning_unit_view.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_view.VOLUME_REMAINING_KEY), learning_unit_view.UNDEFINED_VALUE)

    def test_volumes_unknwon_quadrimester(self):
        entity_component_yr=EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=15,
                                   hourly_volume_partial=-1)
        data = learning_unit_view.volumes(entity_component_yr)
        self.assertEqual(data.get(learning_unit_view.HOURLY_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_view.TOTAL_VOLUME_KEY), 'partial_or_remaining')
        self.assertEqual(data.get(learning_unit_view.VOLUME_PARTIAL_KEY), "(15)")
        self.assertEqual(data.get(learning_unit_view.VOLUME_REMAINING_KEY), "(15)")

    def test_volumes(self):
        entity_component_yr = EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                                         entity_container_year=self.entity_container_yr,
                                                         hourly_volume_total=15,
                                                         hourly_volume_partial=None)
        data = learning_unit_view.volumes(entity_component_yr)
        self.assertEqual(data.get(learning_unit_view.HOURLY_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_view.TOTAL_VOLUME_KEY), learning_unit_view.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_view.VOLUME_PARTIAL_KEY), learning_unit_view.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_view.VOLUME_REMAINING_KEY), learning_unit_view.UNDEFINED_VALUE)

        entity_component_yr = EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                                         entity_container_year=self.entity_container_yr,
                                                         hourly_volume_total=15,
                                                         hourly_volume_partial=15)
        data = learning_unit_view.volumes(entity_component_yr)
        self.assertEqual(data.get(learning_unit_view.HOURLY_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_view.TOTAL_VOLUME_KEY), 'partial')
        self.assertEqual(data.get(learning_unit_view.VOLUME_PARTIAL_KEY), 15)
        self.assertEqual(data.get(learning_unit_view.VOLUME_REMAINING_KEY), '-')

        entity_component_yr = EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                                         entity_container_year=self.entity_container_yr,
                                                         hourly_volume_total=15,
                                                         hourly_volume_partial=10)
        data = learning_unit_view.volumes(entity_component_yr)
        self.assertEqual(data.get(learning_unit_view.HOURLY_VOLUME_KEY), entity_component_yr.hourly_volume_total)
        self.assertEqual(data.get(learning_unit_view.TOTAL_VOLUME_KEY), 'partial_remaining')
        self.assertEqual(data.get(learning_unit_view.VOLUME_PARTIAL_KEY), entity_component_yr.hourly_volume_partial)
        self.assertEqual(data.get(learning_unit_view.VOLUME_REMAINING_KEY), entity_component_yr.hourly_volume_total-entity_component_yr.hourly_volume_partial)

    def test_learning_component_year_undefined_value(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=15.00,
                                   hourly_volume_partial=None)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLA',
                                                     learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), learning_unit_view.UNDEFINED_VALUE)

    def test_learning_component_year_remaining(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=15.00,
                                   hourly_volume_partial=0.00)
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=15.00,
                                   hourly_volume_partial=0.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('remaining'))

    def test_learning_component_year_partial(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=30.00)
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=15.00,
                                   hourly_volume_partial=15.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('partial'))

    def test_learning_component_year_partial_remaining(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=25.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('partial_remaining'))

    def test_learning_component_year_partial_remaining_second(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=30.00)
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_partial=0.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('partial_remaining'))

    def test_learning_component_year_partial_second(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=30.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('partial'))

    def test_learning_component_year_remaining_third(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=0.00)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('remaining'))

    def test_learning_component_yr_unknow_quadrimester(self):
        EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                   entity_container_year=self.entity_container_yr,
                                   hourly_volume_total=30.00,
                                   hourly_volume_partial=-1)
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   acronym='LBIOLA',
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        self.assertEqual(learning_unit_view.volume_distribution(learning_unit_yr), _('partial_or_remaining'))

    def test_learning_unit_usage_two_usages(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLA',
                                                     learning_container_year=learning_container_yr)
        learning_unit_yr_2 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLB',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_2,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_view._learning_unit_usage(learning_component_yr), 'LBIOLA, LBIOLB')

    def test_learning_unit_usage_with_complete_LU(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOL',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_view._learning_unit_usage(learning_component_yr), 'LBIOL')

    def test_learning_unit_usage_by_class_with_complete_LU(self):
        academic_year = AcademicYearFactory(year=2016)
        learning_container_yr = LearningContainerYearFactory(academic_year=academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=academic_year,
                                                     acronym='LBIOL',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        learning_unit_component = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                                               learning_component_year=learning_component_yr)
        learning_class_year = LearningClassYearFactory(learning_component_year=learning_component_yr)
        LearningUnitComponentClassFactory(learning_unit_component=learning_unit_component,
                                          learning_class_year=learning_class_year)
        self.assertEqual(learning_unit_view._learning_unit_usage_by_class(learning_class_year), _('complete'))

    def test_component_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                               learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1", "used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.learning_component_yr.planned_classes, 1)

    def test_component_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1"})
        self.assertRaises(ObjectDoesNotExist, learning_unit_component.LearningUnitComponent.objects.filter(pk=learning_unit_compnt.id).first())

    def test_component_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1", "used_by": "on"})

        self.assertTrue(learning_unit_component.find_by_learning_component_year(self.learning_component_yr).exists())

    def _prepare_context_learning_units_search(self):
        # Create a structure [Entity / Entity version]
        ssh_entity_v = EntityVersionFactory(acronym="SSH", end_date=None)

        agro_entity_v = EntityVersionFactory(parent=ssh_entity_v.entity, acronym="AGRO", end_date=None)
        envi_entity_v = EntityVersionFactory(parent=agro_entity_v.entity, acronym="ENVI", end_date=None)
        ages_entity_v = EntityVersionFactory(parent=agro_entity_v.entity, acronym="AGES", end_date=None)

        espo_entity_v = EntityVersionFactory(parent=ssh_entity_v.entity, acronym="ESPO", end_date=None)
        drt_entity_v = EntityVersionFactory(parent=ssh_entity_v.entity, acronym="DRT", end_date=None)

        # Create UE and put entity charge [AGRO]
        l_container_yr = LearningContainerYearFactory(acronym="LBIR1100", academic_year=self.current_academic_year,
                                                      container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr, entity=agro_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="LBIR1100", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="LBIR1100A", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100B", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100C", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM,
                                status=False)

        # Create another UE and put entity charge [ENV]
        l_container_yr_2 = LearningContainerYearFactory(acronym="CHIM1200", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_2, entity=envi_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="CHIM1200", learning_container_year=l_container_yr_2,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [DRT]
        l_container_yr_3 = LearningContainerYearFactory(acronym="DRT1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_3, entity=drt_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="DRT1500", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="DRT1500A", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)

        # Create another UE and put entity charge [ESPO]
        l_container_yr_4 = LearningContainerYearFactory(acronym="ESPO1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.DISSERTATION)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=espo_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="ESPO1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [AGES]
        l_container_yr_4 = LearningContainerYearFactory(acronym="AGES1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.MASTER_THESIS)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=ages_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="AGES1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=None)

    def test_class_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)

    def test_class_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})

        self.assertTrue(learning_unit_component_class.search(learning_unit_compnt, learning_class_yr).exists())

    def test_class_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)
        a_link = LearningUnitComponentClassFactory(learning_unit_component=learning_unit_compnt,
                                                   learning_class_year=learning_class_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)), data={})

        self.assertRaises(ObjectDoesNotExist, learning_unit_component_class.LearningUnitComponentClass.objects.filter(pk=a_link.id).first())
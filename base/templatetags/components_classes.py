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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django import template
from base.models import learning_unit_component
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.filter
def get_css_class(planned_classes, real_classes):
    planned_classes_int = 0
    real_classes_int = 0

    if planned_classes:
        planned_classes_int = planned_classes

    if real_classes:
        real_classes_int = real_classes

    if planned_classes_int == real_classes_int:
        return "success-color"
    else:
        if planned_classes_int - real_classes_int == 1:
            return "warning-color"

    return "danger-color"


@register.filter
def used_by_partim(learning_component_year, learning_unit_year):
    if learning_unit_component.used_by(learning_component_year, learning_unit_year):
        return _('yes')
    return _('no')



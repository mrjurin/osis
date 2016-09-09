##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib import admin
from base.models import person, attribution
from django.core import serializers
from base.models.serializable_model import SerializableModel


class TutorAdmin(admin.ModelAdmin):
    list_display = ('person', 'changed')
    fieldsets = ((None, {'fields': ('person',)}),)
    raw_id_fields = ('person', )
    search_fields = ['person__first_name', 'person__last_name']


class Tutor(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    person = models.OneToOneField('Person')

    def __str__(self):
        return u"%s" % self.person


def find_by_user(user):
    try:
        pers = person.find_by_user(user)
        tutor = Tutor.objects.get(person=pers)
        return tutor
    except ObjectDoesNotExist:
        return None


def find_by_person(a_person):
    try:
        tutor = Tutor.objects.get(person=a_person)
        return tutor
    except ObjectDoesNotExist:
        return None


def find_by_id(tutor_id):
    return Tutor.objects.get(id=tutor_id)


# To refactor because it is not in the right place.
def find_by_learning_unit(learning_unit_id):
    """
    :param learning_unit_id:
    :return: All tutors of the learningUnit passed in parameter.
    """
    tutor_ids = attribution.search(learning_unit_id=learning_unit_id).values_list('tutor').distinct('tutor')
    return Tutor.objects.filter(pk__in=tutor_ids).order_by('person__last_name', 'person__first_name')


def is_tutor(user):
    """
    :param user:
    :return: True if the user is a tutor. False if the user is not a tutor.
    """
    return Tutor.objects.filter(person__user=user).count() > 0


def find_all_for_sync():
    """
    :return: All records in the 'Student' model (table). Used to synchronize date from Osis to Osis-portal.
    """
    datas = serialize_all_tutors()
    return datas


def serialize_all_tutors():
    """
    Serialize all the tutors in json format
    :return: a json object
    """
    # Fetch all related persons objects
    tutors = Tutor.objects.select_related('person').all()
    datas = []
    for tut in tutors:
        datas.append(({
            'tutors': serialize_list_tutors([tut]),
            'persons': person.serialize_list_persons([tut.person])

        }))
    return datas


def serialize_list_tutors(list_tutors):
    """
    Serialize a list of tutors objects using the json format.
    Use to send data to osis-portal.
    :param list_tutors: a list of tutor objects
    :return: a string
    """
    # Restrict fields for osis-portal
    fields = ('id', 'external_id', 'changed', 'person')
    return serializers.serialize("json", list_tutors, fields=fields,
                                 use_natural_foreign_keys=True,
                                 use_natural_primary_keys=True)


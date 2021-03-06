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
from itertools import chain

from django.db import models
from django.contrib import admin

from base.models.academic_year import current_academic_years
from base.models.enums import structure_type


class StructureAdmin(admin.ModelAdmin):
    list_display = ('acronym', 'title', 'part_of', 'organization', 'type')
    fieldsets = ((None, {'fields': ('acronym', 'title', 'part_of', 'organization', 'type')}),)
    raw_id_fields = ('part_of', )
    search_fields = ['acronym']


class Structure(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15)
    title = models.CharField(max_length=255)
    organization = models.ForeignKey('Organization', null=True)
    part_of = models.ForeignKey('self', null=True, blank=True)
    type = models.CharField(max_length=30, blank=True, null=True, choices=structure_type.TYPES)

    @property
    def children(self):
        return Structure.objects.filter(part_of=self.pk)\
                                .order_by('acronym')

    def serializable_object(self):
        return {
            'id': self.id,
            'acronym': self.acronym,
            'children': [child.serializable_object() for child in self.children]
        }

    def serializable_acronym(self):
        l = []
        l.append(self.acronym)
        for child in self.children:
            l.append(child.acronym)
            child.serializable_acronym()
        return l

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)

    class Meta:
        permissions = (
            ("can_access_structure", "Can access structure"),
        )


def find_structures():
    return Structure.objects.all().order_by('acronym')


def find_by_id(structure_id):
    try:
        return Structure.objects.get(pk=structure_id)
    except:
        return None


def search(acronym=None, title=None, type=None):
    queryset = Structure.objects

    if acronym:
        queryset = queryset.filter(acronym__iexact=acronym)

    if title:
        queryset = queryset.filter(title__icontains=title)

    if type:
        queryset = queryset.filter(type=type)

    return queryset


def find_by_organization(organization):
    return Structure.objects.filter(organization=organization, part_of__isnull=True)


def find_by_type(type):
    return Structure.objects.filter(type__icontains=type)


def find_by_types(types):
    return Structure.objects.filter(type__in=types).order_by('type', 'acronym')


def find_faculty(a_structure):
    if a_structure.type == structure_type.FACULTY:
        return a_structure
    else:
        parent = a_structure.part_of
        if parent:
            if parent.type != structure_type.FACULTY:
                find_faculty(parent)
            else:
                return parent
        return None


def find_first(acronym=None, title=None, type=None):
    return search(acronym, title, type).first()


def find_by_acronyms(acronym_list):
    return Structure.objects.filter(acronym__in=acronym_list).order_by("acronym")


def find_all_structure_parents(entities_manager):
    structures_list = list()
    for entity_manager in entities_manager:
        structures = Structure.objects.filter(acronym=entity_manager.structure.acronym)
        for structure in structures:
            family_list = list(chain(structures, find_all_structure_children(structure)))
            structures_list = list(chain(structures_list, family_list))
    return structures_list


def find_all_structure_children(structure):
    structures_list = list()
    structures = Structure.objects.filter(part_of=structure)
    for structure in structures:
        if structure.part_of:
            children_list = list(chain(structures, find_all_structure_children(structure)))
            structures_list = list(chain(structures_list, children_list))
    return structures_list



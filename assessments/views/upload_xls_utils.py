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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from openpyxl import load_workbook

from assessments.business import score_encoding_list
from assessments.forms.score_file import ScoreFileForm
from attribution import models as mdl_attr
from base import models as mdl
from base.enums import exam_enrollment_justification_type as justification_types

col_academic_year = 0
col_session = 1
col_learning_unit = 2
col_offer = 3
col_registration_id = 4
col_score = 7
col_justification = 8

REGISTRATION_ID_LENGTH = 8

AUTHORIZED_JUSTIFICATION_ALIASES = {
    'T': justification_types.CHEATING,
    'A': justification_types.ABSENCE_UNJUSTIFIED
}

INFORMATIVE_JUSTIFICATION_ALIASES = ['S', 'M']

@login_required
def upload_scores_file(request, learning_unit_year_id=None):
    if request.method == 'POST':
        form = ScoreFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_name = request.FILES['file']
            if file_name is not None:
                learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
                try:
                    __save_xls_scores(request, file_name, learning_unit_year.id)
                except IndexError:
                    messages.add_message(request, messages.ERROR, _('xls_columns_structure_error').format(_('via_excel'), _('get_excel_file')))
        else:
            for error_msg in [error_msg for error_msgs in form.errors.values() for error_msg in error_msgs]:
                messages.add_message(request, messages.ERROR, "{}".format(error_msg))
        return HttpResponseRedirect(reverse('online_encoding', args=[learning_unit_year_id, ]))


def _get_all_data(worksheet):
    """
    :param worksheet: The excel worksheet (containing examEnrollments/scores)
    :return: All learn_unit_acronyms, offer_acronyms, registration_ids, session and academic_years
             in all lines of the worksheet.
    """
    learn_unit_acronyms = []
    offer_acronyms = []
    registration_ids = []
    sessions = []
    academic_years = []

    for count, row in enumerate(worksheet.rows):
        if not _is_valid_registration_id(row):
            # In case of blank line or line that is not a examEnrollment
            continue
        session = row[col_session].value
        session = int(session) if isinstance(session, str) and session.isdigit() else session
        if session and session not in sessions:
            sessions.append(session)

        try:
            academic_year = None
            if type(row[col_academic_year].value) is int:
                academic_year = int(row[col_academic_year].value)
            elif type(row[col_academic_year].value) is str:
                academic_year = int(row[col_academic_year].value[:4])
            if academic_year and academic_year not in academic_years:
                academic_years.append(academic_year)
        except (ValueError, TypeError):
            pass

        learn_unit_acronym = row[col_learning_unit].value
        if learn_unit_acronym and learn_unit_acronym not in learn_unit_acronyms:
            learn_unit_acronyms.append(learn_unit_acronym)

        offer_acronym = row[col_offer].value
        if offer_acronym and offer_acronym not in offer_acronyms:
            offer_acronyms.append(offer_acronym)

        registration_id = row[col_registration_id].value
        if registration_id and registration_id not in registration_ids:
            registration_ids.append(registration_id)

    return {'learning_unit_acronyms': learn_unit_acronyms,
            'offer_acronyms': offer_acronyms,
            'registration_ids': registration_ids,
            'sessions': sessions,
            'academic_years': academic_years}


def __save_xls_scores(request, file_name, learning_unit_year_id):
    try:
        workbook = load_workbook(file_name, read_only=True)
    except KeyError:
        messages.add_message(request, messages.ERROR, _('file_must_be_xlsx'))
        return False
    worksheet = workbook.active
    new_scores_number = 0
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    is_program_manager = mdl.program_manager.is_program_manager(request.user)

    data_xls = _get_all_data(worksheet)

    try:
        data_xls['session'] = _extract_session_number(data_xls)
        data_xls['academic_year'] = _extract_academic_year(data_xls)
    except Exception as e:
        messages.add_message(request, messages.ERROR, _(e.args[0]))
        return False

    academic_year_in_database = mdl.academic_year.find_academic_year_by_year(data_xls['academic_year'])
    if not academic_year_in_database:
        messages.add_message(request, messages.ERROR, '%s (%s).' % (_('no_data_for_this_academic_year'), data_xls['academic_year']))
        return False

    score_list = score_encoding_list.get_scores_encoding_list(
        user=request.user,
        learning_unit_year_id=learning_unit_year_id
    )

    offer_acronyms_managed_by_user = {offer_year.acronym for offer_year
                                      in score_encoding_list.find_related_offer_years(score_list)}
    learn_unit_acronyms_managed_by_user = {learning_unit_year.acronym for learning_unit_year
                                            in score_encoding_list.find_related_learning_unit_years(score_list)}
    registration_ids_managed_by_user = score_encoding_list.find_related_registration_ids(score_list)

    enrollments_grouped = _group_exam_enrollments_by_registration_id_and_learning_unit_year(score_list.enrollments)

    # Iterates over the lines of the spreadsheet.
    for count, row in enumerate(worksheet.rows):
        if _row_can_be_ignored(row):
            continue

        xls_registration_id = _extract_registration_id(row)
        info_line = "%s %d (NOMA %s):" % (_('Line'), count + 1 , xls_registration_id)
        try:
            _check_intergity_data(row,
                                  offer_acronyms_managed=offer_acronyms_managed_by_user,
                                  learn_unit_acronyms_managed = learn_unit_acronyms_managed_by_user,
                                  registration_ids_managed = registration_ids_managed_by_user,
                                  learning_unit_year=learning_unit_year)
            updated_row = _update_row(request.user, row, enrollments_grouped, is_program_manager)
            if updated_row:
                new_scores_number+=1
        except ValidationError as e:
            messages.add_message(request, messages.ERROR, "%s %s" % (info_line,_(e.messages[0])))
        except UploadValueError as e:
            messages.add_message(request, e.message, "%s %s" % (info_line,_(e.value)))
        except Exception as e:
            messages.add_message(request, messages.ERROR, "%s %s" % (info_line, _(e.args[0])))

    if new_scores_number:
        messages.add_message(request, messages.SUCCESS, '%s %s' % (str(new_scores_number), _('score_saved')))
        if not is_program_manager:
            __warn_that_score_responsibles_must_submit_scores(request, learning_unit_year)
        return True
    else:
        messages.add_message(request, messages.ERROR, '%s' % _('no_score_injected'))
        return False


def _extract_session_number(data_xls):
    if len(data_xls['sessions']) > 1:
        raise UploadValueError('more_than_one_session_error', messages.ERROR)
    elif len(data_xls['sessions']) == 0:
        raise UploadValueError('missing_column_session', messages.ERROR)
    return data_xls['sessions'][0] # Only one session


def _extract_academic_year(data_xls):
    if len(data_xls['academic_years']) > 1:
        raise UploadValueError('more_than_one_academic_year_error', messages.ERROR)
    elif len(data_xls['academic_years']) == 0:
        raise UploadValueError('no_valid_academic_year_error', messages.ERROR)

    return data_xls['academic_years'][0]  # Only one academic year


def _extract_registration_id(row):
    if _is_valid_registration_id(row):
        xls_registration_id = str(row[col_registration_id].value)
        return xls_registration_id.zfill(REGISTRATION_ID_LENGTH)
    return None


def _group_exam_enrollments_by_registration_id_and_learning_unit_year(enrollments):
    exam_enrollments_by_registration_id = {}
    for enrollment in enrollments:
        key = "{}_{}".format(enrollment.learning_unit_enrollment.student.registration_id,
                             enrollment.learning_unit_enrollment.learning_unit_year.acronym)
        exam_enrollments_by_registration_id.setdefault(key, []).append(enrollment)
    return exam_enrollments_by_registration_id


def _row_can_be_ignored(row):
    return not _is_valid_registration_id(row) or _is_empty_row(row)


def _is_valid_registration_id(row):
    registration_id_value = row[col_registration_id].value
    return registration_id_value and str(registration_id_value).isdigit()


def _is_empty_row(row):
    return (row[col_score].value is None or row[col_score].value == '') and not row[col_justification].value


def _check_intergity_data(row, **kwargs):
    xls_registration_id = _extract_registration_id(row)
    xls_offer_year_acronym = row[col_offer].value
    xls_learning_unit_acronym = row[col_learning_unit].value
    registration_ids_managed = kwargs.get('registration_ids_managed')
    learn_unit_acronyms_managed = kwargs.get('learn_unit_acronyms_managed')
    offer_acronyms_managed = kwargs.get('offer_acronyms_managed')
    learning_unit_year = kwargs.get('learning_unit_year')

    if xls_registration_id not in registration_ids_managed:
        # In case the xls registration_id is not in the list, we check...
        if xls_learning_unit_acronym not in learn_unit_acronyms_managed:
            # ... if it is because the user doesn't have access to the learningUnit
            raise UploadValueError("'%s' %s!" % (xls_learning_unit_acronym, _('learning_unit_not_access_or_not_exist')),
                                   messages.ERROR)
        elif learning_unit_year.acronym != xls_learning_unit_acronym:
            # ... if it is because the user has multiple learningUnit in his excel file
            # (the data from the DataBase are filtered by LearningUnitYear because excel file is build by learningUnit)
            raise UploadValueError("%s" % _('more_than_one_learning_unit_error'), messages.ERROR)
        elif xls_offer_year_acronym not in offer_acronyms_managed:
            # ... if it is because the user haven't access rights to the offerYear
            raise UploadValueError("'%s' %s!" % (xls_offer_year_acronym, _('offer_year_not_access_or_not_exist')),
                                   messages.ERROR)
        else:
            # ... if it's beacause the registration id doesn't exist
            raise UploadValueError("%s" % _('registration_id_not_access_or_not_exist'), messages.ERROR)


def _update_row(user, row, enrollments_managed_grouped, is_program_manager):
    xls_registration_id = _extract_registration_id(row)
    xls_learning_unit_acronym = row[col_learning_unit].value
    xls_score = row[col_score].value
    xls_justification = row[col_justification].value

    key = "{}_{}".format(xls_registration_id, xls_learning_unit_acronym)
    enrollments = enrollments_managed_grouped.get(key, [])

    if not enrollments:
        raise ValueError("%s!" % _('enrollment_activity_not_exist') % (xls_learning_unit_acronym))

    enrollment = enrollments[0]

    if score_encoding_list.is_deadline_reached(enrollment, is_program_manager):
        raise UploadValueError("%s!" % _('deadline_reached'), messages.ERROR)

    if not is_program_manager and enrollment.is_final:
        raise UploadValueError("%s!" %  _('score_already_submitted'), messages.WARNING)

    if xls_score is not None and xls_justification:
        raise UploadValueError("%s!" %  _('constraint_score_other_score'), messages.ERROR)

    enrollment.score_encoded = xls_score
    enrollment.justification_encoded = None
    if xls_justification:
        enrollment.justification_encoded = _get_justification_from_aliases(enrollment, xls_justification)

    return score_encoding_list.update_enrollment(
        enrollment=enrollment,
        user=user
    )


def __warn_that_score_responsibles_must_submit_scores(request, learning_unit_year):
    tutor = mdl.tutor.find_by_user(request.user)
    if tutor and not mdl_attr.attribution.is_score_responsible(request.user, learning_unit_year):
        messages.add_message(request, messages.SUCCESS, '%s' % _('scores_responsible_must_still_submit_scores'))


def _get_justification_from_aliases(enrollment, justification_encoded):
    # When absence justified no change
    if enrollment.justification_final == justification_types.ABSENCE_JUSTIFIED:
        return justification_types.ABSENCE_JUSTIFIED

    # Don't care about S/M
    if justification_encoded in INFORMATIVE_JUSTIFICATION_ALIASES:
        return None

    justification = AUTHORIZED_JUSTIFICATION_ALIASES.get(justification_encoded)
    if justification:
        return justification
    else:
        raise UploadValueError('%s' % _('justification_invalid_value'), messages.ERROR)


class UploadValueError(ValueError):
    def __init__(self, value, message):
        self.value = value
        self.message = message
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
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.utils import timezone
from assessments.business.score_encoding_list import ScoresEncodingList

from base.tests.models import test_exam_enrollment, test_offer_enrollment, \
    test_learning_unit_enrollment, test_session_exam, test_offer_year
from attribution.tests.models import test_attribution
from assessments.views import score_encoding
from base.models.enums import number_session, academic_calendar_type
from base.models.exam_enrollment import ExamEnrollment

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.student import StudentFactory


class OnlineEncodingTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        academic_year = AcademicYearFactory(year=timezone.now().year - 1)
        academic_calendar = AcademicCalendarFactory.build(title="Submission of score encoding - 1",
                                                          start_date=academic_year.start_date,
                                                          end_date=academic_year.end_date,
                                                          academic_year=academic_year,
                                                          reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        academic_calendar.save(functions=[])
        SessionExamCalendarFactory(academic_calendar=academic_calendar, number_session=number_session.ONE)

        self.learning_unit_year = LearningUnitYearFactory(academic_year=academic_year)
        self.offer_year = test_offer_year.create_offer_year('SINF1BA', 'Bachelor in informatica', academic_year)
        self.session_exam = test_session_exam.create_session_exam(number_session.ONE, self.learning_unit_year,
                                                                  self.offer_year)

        # Create enrollment related
        self.enrollments = []
        for index in range(0,2):
            offer_year = OfferYearFactory(academic_year=academic_year)
            OfferYearCalendarFactory(academic_calendar=academic_calendar, offer_year=offer_year)
            offer_enrollment = test_offer_enrollment.create_offer_enrollment(StudentFactory(), offer_year)
            learning_unit_enrollment = test_learning_unit_enrollment.create_learning_unit_enrollment(
                                                                       offer_enrollment=offer_enrollment,
                                                                       learning_unit_year=self.learning_unit_year)
            exam_enrollment = test_exam_enrollment.create_exam_enrollment(self.session_exam, learning_unit_enrollment)
            self.enrollments.append(exam_enrollment)

        self.tutor = TutorFactory()
        test_attribution.create_attribution(tutor=self.tutor, learning_unit_year=self.learning_unit_year)
        add_permission(self.tutor.person.user, "can_access_scoreencoding")

        offer_year = self.enrollments[0].learning_unit_enrollment.offer_enrollment.offer_year
        self.program_manager_1 = ProgramManagerFactory(offer_year=offer_year)
        add_permission(self.program_manager_1.person.user, "can_access_scoreencoding")

        offer_year = self.enrollments[1].learning_unit_enrollment.offer_enrollment.offer_year
        self.program_manager_2 = ProgramManagerFactory(offer_year=offer_year)
        add_permission(self.program_manager_2.person.user, "can_access_scoreencoding")

    def test_filter_enrollments_by_offer_year(self):
        enrollments = self.enrollments

        expected = [self.enrollments[0]]
        offer_year = self.enrollments[0].learning_unit_enrollment.offer_enrollment.offer_year
        actual = score_encoding.filter_enrollments_by_offer_year(enrollments, offer_year)

        self.assertListEqual(expected, actual, "Should only return enrollments for the first offer year")

    def test_tutor_encoding_with_a_student(self):
        self.client.force_login(self.tutor.person.user)
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        response = self.client.post(url, data=self.get_form_with_one_student_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, None, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, None, None)

    def test_tutor_encoding_final_scores_for_a_student(self):
        self.client.force_login(self.tutor.person.user)
        self.enrollments[0].score_final = 16
        self.enrollments[0].score_draft = 16
        self.enrollments[0].save()
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_one_student_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 16, 16, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, None, None)

    def test_pgm_encoding_for_a_student(self):
        self.client.force_login(self.program_manager_1.person.user)
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_one_student_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, 15, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, None, None)

    def test_pgm_encoding_with_justification_for_a_student(self):
        self.client.force_login(self.program_manager_2.person.user)
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled_and_one_with_justification())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], None, None, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, "ABSENCE_JUSTIFIED", "ABSENCE_JUSTIFIED")

    def test_tutor_encoding_with_all_students(self):
        self.client.force_login(self.tutor.person.user)
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, None, None, None)
        self.assert_exam_enrollments(self.enrollments[1], 18, None, None, None)

    def test_tutor_double_encoding_with_all_students(self):
        self.client.force_login(self.tutor.person.user)
        prepare_exam_enrollment_for_double_encoding_validation(self.enrollments[0])
        prepare_exam_enrollment_for_double_encoding_validation(self.enrollments[1])
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, None, None, None)
        self.assert_exam_enrollments(self.enrollments[1], 18, None, None, None)

    def test_tutor_encoding_with_all_students_and_a_justification(self):
        self.client.force_login(self.tutor.person.user)
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled_and_one_with_justification())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, None, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, "ABSENCE_JUSTIFIED", None)

    def test_pgm_double_encoding_for_a_student(self):
        self.client.force_login(self.program_manager_1.person.user)
        url = reverse('online_double_encoding_validation', args=[self.learning_unit_year.id])
        prepare_exam_enrollment_for_double_encoding_validation(self.enrollments[0])
        self.client.post(url, data=self.get_form_with_one_student_filled())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, 15, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, None, None)

    def test_encoding_by_specific_criteria(self):
        self.client.force_login(self.program_manager_1.person.user)
        url = reverse('specific_criteria_submission')
        self.client.post(url, data=self.get_form_for_specific_criteria())

        self.refresh_exam_enrollments_from_db()
        self.assert_exam_enrollments(self.enrollments[0], 15, 15, None, None)
        self.assert_exam_enrollments(self.enrollments[1], None, None, None, None)

    @patch("assessments.views.score_encoding._extract_id_from_post_data")
    @patch("assessments.business.score_encoding_list.get_scores_encoding_list")
    def test_encoding_by_specific_criteria_case_no_changes_in_form(self, mock_scores_encoding_list, mock_id_from_post_data):
        mock_scores_encoding_list.return_value = ScoresEncodingList()
        mock_id_from_post_data.return_value = []
        request = self.request_factory.get(reverse('specific_criteria_submission'))
        request.user = self.tutor.person.user
        scores_encoding_object = score_encoding._get_score_encoding_list_with_only_enrollment_modified(request)
        self.assertEqual(scores_encoding_object.enrollments, [])

    @patch("base.utils.send_mail.send_message_after_all_encoded_by_manager")
    def test_email_after_encoding_all_students_for_offer_year(self, mock_send_email):
        self.client.force_login(self.program_manager_1.person.user)
        mock_send_email.return_value = None
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled())

        self.assertTrue(mock_send_email.called)
        (persons, enrollments, learning_unit_acronym, offer_acronym), kwargs = mock_send_email.call_args
        self.assertEqual(persons, [self.tutor.person])
        self.assertEqual(enrollments, [self.enrollments[0]])
        self.assertEqual(learning_unit_acronym, self.learning_unit_year.acronym)
        offer_year = self.enrollments[0].learning_unit_enrollment.offer_enrollment.offer_year
        self.assertEqual(offer_acronym, offer_year.acronym)

    @patch("base.utils.send_mail.send_message_after_all_encoded_by_manager")
    def test_email_after_encoding_all_students_for_offer_year_with_justification(self, mock_send_email):
        self.client.force_login(self.program_manager_2.person.user)
        mock_send_email.return_value = None
        url = reverse('online_encoding_form', args=[self.learning_unit_year.id])
        self.client.post(url, data=self.get_form_with_all_students_filled_and_one_with_justification())

        self.assertTrue(mock_send_email.called)
        (persons, enrollments, learning_unit_acronym, offer_acronym), kwargs = mock_send_email.call_args
        self.assertEqual(persons, [self.tutor.person])
        self.assertEqual(enrollments, [self.enrollments[1]])
        self.assertEqual(learning_unit_acronym, self.learning_unit_year.acronym)
        offer_year = self.enrollments[1].learning_unit_enrollment.offer_enrollment.offer_year
        self.assertEqual(offer_acronym, offer_year.acronym)

    def assert_exam_enrollments(self, exam_enrollment, score_draft, score_final, justification_draft,
                                justification_final):
        self.assertEqual(exam_enrollment.score_draft, score_draft)
        self.assertEqual(exam_enrollment.score_final, score_final)
        self.assertEqual(exam_enrollment.justification_draft, justification_draft)
        self.assertEqual(exam_enrollment.justification_final, justification_final)

    def get_form_with_one_student_filled(self):
        exam_enrollment_1 = self.enrollments[0]
        exam_enrollment_2 = self.enrollments[1]

        return {"score_" + str(exam_enrollment_1.id): "15",
                "justification_" + str(exam_enrollment_1.id): "",
                "score_changed_" + str(exam_enrollment_1.id): "true",
                "score_" + str(exam_enrollment_2.id): "",
                "justification_" + str(exam_enrollment_2.id): "",
                "score_changed_" + str(exam_enrollment_2.id): "false"
                }

    def get_form_with_all_students_filled(self):
        exam_enrollment_1 = self.enrollments[0]
        exam_enrollment_2 = self.enrollments[1]

        return {"score_" + str(exam_enrollment_1.id): "15",
                "justification_" + str(exam_enrollment_1.id): "",
                "score_changed_" + str(exam_enrollment_1.id): "true",
                "score_" + str(exam_enrollment_2.id): "18",
                "justification_" + str(exam_enrollment_2.id): "",
                "score_changed_" + str(exam_enrollment_2.id): "true"
                }

    def get_form_with_all_students_filled_and_one_with_justification(self):
        exam_enrollment_1 = self.enrollments[0]
        exam_enrollment_2 = self.enrollments[1]

        return {"score_" + str(exam_enrollment_1.id): "15",
                "justification_" + str(exam_enrollment_1.id): "",
                "score_changed_" + str(exam_enrollment_1.id): "true",
                "score_" + str(exam_enrollment_2.id): "",
                "justification_" + str(exam_enrollment_2.id): "ABSENCE_JUSTIFIED",
                "score_changed_" + str(exam_enrollment_2.id): "true"
                }

    def get_form_for_specific_criteria(self):
        exam_enrollment = self.enrollments[0]
        offer_year = exam_enrollment.learning_unit_enrollment.offer_enrollment.offer_year
        return {"score_" + str(exam_enrollment.id): "15",
                "justification_" + str(exam_enrollment.id): "",
                "score_changed_" + str(exam_enrollment.id): "true",
                "program": str(offer_year.id)
                }

    def refresh_exam_enrollments_from_db(self):
        for enrollment in self.enrollments:
            enrollment.refresh_from_db()


class OutsideEncodingPeriodTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='score_encoding', password='score_encoding')
        add_permission(self.user, "can_access_scoreencoding")
        self.client.force_login(self.user)

        # Create context
        academic_year = AcademicYearFactory(year=timezone.now().year - 1)
        academic_calendar = AcademicCalendarFactory.build(title="Submission of score encoding - 1",
                                                          academic_year=academic_year,
                                                          reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        academic_calendar.save(functions=[])
        self.session_exam_calendar = SessionExamCalendarFactory(academic_calendar=academic_calendar,
                                                                number_session=number_session.ONE)

    def test_redirection_to_current_exam_session(self):
        url = reverse('outside_scores_encodings_period')
        response = self.client.get(url)
        self.assertRedirects(response, "%s?next=%s" % (reverse('scores_encoding'), reverse('outside_scores_encodings_period')))  # Redirection

    def test_redirection_to_outside_encoding_period(self):
        self.session_exam_calendar.delete()
        url = reverse('scores_encoding')
        response = self.client.get(url)
        self.assertRedirects(response, "%s?next=%s" % (reverse('outside_scores_encodings_period'), reverse('scores_encoding')))  # Redirection


class GetScoreEncodingViewProgramManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='score_encoding', password='score_encoding')
        self.person = PersonFactory(user=self.user)
        add_permission(self.user, "can_access_scoreencoding")
        self.client.force_login(self.user)

        # Set user as program manager of two offer
        academic_year = AcademicYearFactory(year=timezone.now().year - 1)
        self.offer_year_bio2ma = OfferYearFactory(acronym="BIO2MA", title="Master en Biologie",
                                                  academic_year=academic_year)
        self.offer_year_bio2bac = OfferYearFactory(acronym="BIO2BAC", title="Bachelier en Biologie",
                                                   academic_year=academic_year)
        ProgramManagerFactory(offer_year=self.offer_year_bio2ma, person=self.person)
        ProgramManagerFactory(offer_year=self.offer_year_bio2bac, person=self.person)

        # Create an score submission event - with an session exam
        academic_calendar = AcademicCalendarFactory.build(title="Submission of score encoding - 1",
                                                          academic_year=academic_year,
                                                          start_date=academic_year.start_date,
                                                          end_date=academic_year.end_date,
                                                          reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        academic_calendar.save(functions=[])
        self.session_exam_calendar = SessionExamCalendarFactory(academic_calendar=academic_calendar,
                                                                number_session=number_session.ONE)

        # Offer : BIO2MA - 2 Learning unit with exam
        self.offer_year_calendar_bio2ma = OfferYearCalendarFactory(offer_year=self.offer_year_bio2ma,
                                                                   academic_calendar=academic_calendar)

        self.learning_unit_year = LearningUnitYearFactory(academic_year=academic_year)
        self.learning_unit_year_2 = LearningUnitYearFactory(academic_year=academic_year)
        self.first_session_exam = test_session_exam.create_session_exam(number_session.ONE,
                                                                        self.learning_unit_year,
                                                                        self.offer_year_bio2ma)
        self.first_session_exam_2 = test_session_exam.create_session_exam(number_session.ONE,
                                                                          self.learning_unit_year_2,
                                                                          self.offer_year_bio2ma)

        # Offer: BIO2BAC - 1 learning unit with exam
        self.offer_year_calendar_bio2bac = OfferYearCalendarFactory(offer_year=self.offer_year_bio2ma,
                                                                    academic_calendar=academic_calendar)
        self.learning_unit_year_3 = LearningUnitYearFactory(academic_year=academic_year)
        self.first_session_exam_3 = test_session_exam.create_session_exam(number_session.ONE,
                                                                          self.learning_unit_year_3,
                                                                          self.offer_year_bio2bac)

        self._create_context_exam_enrollment()

    def test_get_score_encoding_list_empty(self):
        ExamEnrollment.objects.all().delete() #remove all exam enrolment [No subscription to exam]
        url = reverse('scores_encoding')
        response = self.client.get(url)
        context = response.context[-1]
        self.assertEqual(response.status_code, 200)
        self.assertFalse(context['notes_list'])

    def test_get_score_encoding(self):
        url = reverse('scores_encoding')
        response = self.client.get(url)
        context = response.context[-1]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(context['notes_list']), 3)

    def _create_context_exam_enrollment(self):
        self.students = []
        for index in range(0, 20):
            self.students.append(StudentFactory())
            if index < 5:
                # For the 5 first students register to the BIO2MA
                offer_enrollment = test_offer_enrollment.create_offer_enrollment(self.students[index],
                                                                                 self.offer_year_bio2ma)
                learning_unit_enrollment = test_learning_unit_enrollment.create_learning_unit_enrollment(
                                                                              offer_enrollment=offer_enrollment,
                                                                              learning_unit_year=self.learning_unit_year)
                learning_unit_enrollment_2 = test_learning_unit_enrollment.create_learning_unit_enrollment(
                                                                            offer_enrollment=offer_enrollment,
                                                                            learning_unit_year=self.learning_unit_year_2)
                test_exam_enrollment.create_exam_enrollment(self.first_session_exam, learning_unit_enrollment)
                test_exam_enrollment.create_exam_enrollment(self.first_session_exam_2, learning_unit_enrollment_2)
            else:
                # For the other register to the BIO2BAC
                offer_enrollment = test_offer_enrollment.create_offer_enrollment(self.students[index], self.offer_year_bio2bac)
                learning_unit_enrollment = test_learning_unit_enrollment.create_learning_unit_enrollment(offer_enrollment=offer_enrollment,
                                                                                                         learning_unit_year=self.learning_unit_year_3)
                test_exam_enrollment.create_exam_enrollment(self.first_session_exam_3, learning_unit_enrollment)


class UploadXLSTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='score_encoding', password='score_encoding')
        add_permission(self.user, "can_access_scoreencoding")
        self.client.force_login(self.user)

    def test_method_not_allowed_upload_xlsx(self):
        from assessments.views.upload_xls_utils import upload_scores_file
        url = reverse(upload_scores_file, kwargs={
            'learning_unit_year_id': '1',
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)


def prepare_exam_enrollment_for_double_encoding_validation(exam_enrollment):
    exam_enrollment.score_reencoded = 14
    exam_enrollment.score_draft = 14
    exam_enrollment.save()


def add_permission(user, codename):
    perm = get_permission(codename)
    user.user_permissions.add(perm)


def get_permission(codename):
    return Permission.objects.filter(codename=codename).first()

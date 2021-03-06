# Copyright 2013 UNED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import date, datetime, timedelta
import urllib

import boto
import pymongo

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from moocng.api.mongodb import get_db
from moocng.api.tasks import on_peerreviewreview_created_task
from moocng.courses.models import KnowledgeQuantum
from moocng.courses.utils import send_mail_wrapper, is_course_ready, has_user_passed_course, get_group_by_user_and_course, is_teacher as is_teacher_test
from moocng.courses.security import get_course_if_user_can_view_or_404, get_tasks_available_for_user, get_course_progress_for_user
from moocng.peerreview.forms import ReviewSubmissionForm, EvalutionCriteriaResponseForm
from moocng.peerreview.models import PeerReviewAssignment, EvaluationCriterion
from moocng.peerreview.utils import (course_get_visible_peer_review_assignments, save_review,
                                    insert_p2p_if_does_not_exists_or_raise)


@login_required
def course_review_assign(request, course_slug, assignment_id):
    course = get_course_if_user_can_view_or_404(course_slug, request)
    assignment = get_object_or_404(PeerReviewAssignment, id=assignment_id)
    user_id = request.user.id

    is_enrolled = course.students.filter(id=user_id).exists()
    if not is_enrolled:
        messages.error(request, _('You are not enrolled in this course'))
        return HttpResponseRedirect(reverse('course_overview', args=[course_slug]))

    if assignment.kq.unit.course != course:
        messages.error(request, _('The selected peer review assignment is not part of this course.'))
        return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))

    collection = get_db().get_collection('peer_review_submissions')

    submission = collection.find({
        'kq': assignment.kq.id,
        'assigned_to': user_id
    })
    if submission.count() > 0:
        messages.error(request, _('You already have a submission assigned.'))
        return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))

    max_hours_assigned = timedelta(hours=getattr(settings,
                                   "PEER_REVIEW_ASSIGNATION_EXPIRE", 24))

    assignation_expire = datetime.utcnow() - max_hours_assigned

    #Check number of course langs to assign a PeerReview
    is_user_lang_valid = False
    if course.languages.count() > 1:
        for lang in course.languages.all():
            if request.user.get_profile().language == lang.abbr:
                is_user_lang_valid = True
        if is_user_lang_valid:
            submission = _get_peer_review_submission(user_id, assignment.kq.id, assignation_expire, request.user.get_profile().language)
        else:
            submission = _get_peer_review_submission(user_id, assignment.kq.id, assignation_expire)
    else:
        submission = _get_peer_review_submission(user_id, assignment.kq.id, assignation_expire)

    if submission.count() == 0:
        # Deactivate while it is finished
        #if course.languages.count() > 1 and is_user_lang_valid:
        #    return HttpResponseRedirect(reverse('course_reviews_ignorelang', args=[course_slug, assignment.kq.id]))
        messages.error(request, _('There is no submission avaliable for you at this moment. Please, try again later.'))
        return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))
    else:
        collection.update({
            '_id': submission[0]['_id']
        }, {
            '$set': {
                'assigned_to': user_id,
                'assigned_when': datetime.utcnow()
            }
        })
        return HttpResponseRedirect(reverse('course_review_review', args=[course_slug, assignment_id]))


@login_required
def course_reviews(request, course_slug, kq_id=None, ignore_langs=False):
    course = get_course_if_user_can_view_or_404(course_slug, request)

    is_enrolled = course.students.filter(id=request.user.id).exists()
    if not is_enrolled:
        messages.error(request, _('You are not enrolled in this course'))
        return HttpResponseRedirect(reverse('course_overview', args=[course_slug]))

    is_ready, ask_admin, is_outdated = is_course_ready(course)
    is_teacher = is_teacher_test(request.user, course)

    if not is_ready and not is_teacher and not request.user.is_staff and not request.user.is_superuser:
        return render_to_response('courses/no_content.html', {
            'course': course,
            'is_enrolled': is_enrolled,
            'ask_admin': ask_admin,
        }, context_instance=RequestContext(request))

    assignments = course_get_visible_peer_review_assignments(request.user,
                                                             course)

    collection = get_db().get_collection('peer_review_submissions')
    submissions = collection.find({
        'author': request.user.id,
        'course': course.id,
    }, {'kq': True, '_id': False})
    submissions = [s['kq'] for s in submissions]

    user_submissions = [a.id for a in assignments if a.kq.id in submissions]
    tasks = get_tasks_available_for_user(course, request.user)
    group = get_group_by_user_and_course(request.user.id, course.id)

    return render_to_response('peerreview/reviews.html', {
        'course': course,
        'assignments': assignments,
        'user_submissions': user_submissions,
        'kq_id': kq_id,
        'ignore_langs': ignore_langs,
        'is_enrolled': is_enrolled,
        'is_ready': is_ready,
        'is_outdated': is_outdated,
        'can_review': date.today() < course.end_date+timedelta(days=14),
        'task_list': tasks[0],
        'tasks_done': tasks[1],
        'progress': get_course_progress_for_user(course, request.user),
        'passed': has_user_passed_course(request.user, course),
        'group': group,
    }, context_instance=RequestContext(request))


@login_required
def course_review_review(request, course_slug, assignment_id):
    course = get_course_if_user_can_view_or_404(course_slug, request)
    assignment = get_object_or_404(PeerReviewAssignment, id=assignment_id)
    user_id = request.user.id

    is_enrolled = course.students.filter(id=user_id).exists()
    if not is_enrolled:
        messages.error(request, _('You are not enrolled in this course'))
        return HttpResponseRedirect(reverse('course_overview', args=[course_slug]))

    if assignment.kq.unit.course != course:
        messages.error(request, _('The selected peer review assignment is not part of this course.'))
        return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))

    collection = get_db().get_collection('peer_review_submissions')

    submission = collection.find({
        'kq': assignment.kq.id,
        'assigned_to': user_id
    })

    if submission.count() == 0:
        messages.error(request, _('You don\'t have this submission assigned.'))
        return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))

    submission_obj = submission[0]

    submitter = User.objects.get(id=int(submission_obj['author']))

    criteria_initial = [{'evaluation_criterion_id': criterion.id} for criterion in assignment.criteria.all()]
    EvalutionCriteriaResponseFormSet = formset_factory(EvalutionCriteriaResponseForm, extra=0, max_num=len(criteria_initial))

    if request.method == "POST":
        submission_form = ReviewSubmissionForm(request.POST)
        criteria_formset = EvalutionCriteriaResponseFormSet(request.POST, initial=criteria_initial)
        if criteria_formset.is_valid() and submission_form.is_valid():
            criteria_values = [(int(form.cleaned_data['evaluation_criterion_id']), int(form.cleaned_data['value'])) for form in criteria_formset]
            try:
                review = save_review(assignment.kq, request.user, submitter, criteria_values, submission_form.cleaned_data['comments'])

                reviews = get_db().get_collection('peer_review_reviews')
                reviewed_count = reviews.find({
                    'reviewer': user_id,
                    'kq': assignment.kq.id
                }).count()

                review_scores = [int(form.cleaned_data['value']) for form in criteria_formset]
                if len(review_scores) > 0:
                    score = float(sum(review_scores) / len(review_scores)) * 2 / 10
                else:
                    score = 1
                extra = {
                    'geolocation': {
                        'lat': float(request.POST.get("context_geo_lat", "0.0")),
                        'lon': float(request.POST.get("context_geo_lon", "0.0")),
                    },
                    'url': request.build_absolute_uri(),
                    'result': {
                        'score': score,
                        'comment': submission_form.cleaned_data['comments']
                    }
                }
                on_peerreviewreview_created_task.apply_async(
                    args=[review, reviewed_count, extra],
                    queue='stats',
                )

                current_site_name = get_current_site(request).name
                send_mail_to_submission_owner(current_site_name, assignment, review, submitter)
            except IntegrityError:
                messages.error(request, _('Your can\'t submit two times the same review.'))
                return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))

            pending = assignment.minimum_reviewers - reviewed_count
            if pending > 0:
                messages.success(request, _('Your review has been submitted. You have to review at least %d exercises more.') % pending)
            else:
                messages.success(request, _('Your review has been submitted.'))
            return HttpResponseRedirect(reverse('course_reviews', args=[course_slug]))
    else:
        submission_form = ReviewSubmissionForm()
        criteria_formset = EvalutionCriteriaResponseFormSet(initial=criteria_initial)

    max_hours_assigned = timedelta(hours=getattr(settings,
                                   "PEER_REVIEW_ASSIGNATION_EXPIRE", 24))

    assigned_when = submission[0]["assigned_when"]
    assignation_expire = assigned_when + max_hours_assigned

    now = datetime.now(assigned_when.tzinfo)
    is_assignation_expired = now > assignation_expire

    return render_to_response('peerreview/review_review.html', {
        'submission': submission[0],
        'is_assignation_expired': is_assignation_expired,
        'assignation_expire': assignation_expire,
        'submission_form': submission_form,
        'criteria_formset': criteria_formset,
        'course': course,
        'assignment': assignment,
        'is_enrolled': is_enrolled,
    }, context_instance=RequestContext(request))


def send_mail_to_submission_owner(current_site_name, assignment, review, submitter):
    subject = _(u'Your assignment "%(nugget)s" has been reviewed') % {'nugget': assignment.kq.title}
    template = 'peerreview/email_review_submission.txt'
    review_criteria = []
    for item in review['criteria']:
        try:
            criterion = EvaluationCriterion.objects.get(pk=item[0]).title
        except:
            criterion = _(u'Undefined')

        review_criteria.append((criterion, item[1]))

    context = {
        'user': submitter,
        'date': review['created'].strftime('%d/%m/%Y'),
        'nugget': assignment.kq,
        'review_criteria': review_criteria,
        'comment': review['comment'],
        'site': current_site_name
    }

    to = [submitter.email]

    send_mail_wrapper(subject, template, context, to)


@login_required
def get_s3_upload_url(request):
    user = request.user

    filename = request.GET.get('name', 'noname')
    kq_id = request.GET.get('kq', 'nokq')

    name = "%d/%s/%s" % (user.id, kq_id, filename)
    mime_type = request.GET['type']
    headers = {
        'x-amz-acl': "public-read",
        'Content-Type': mime_type,
    }

    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    url = conn.generate_url(
        settings.AWS_S3_UPLOAD_EXPIRE_TIME,
        "PUT",
        settings.AWS_STORAGE_BUCKET_NAME,
        name,
        headers
    )

    return HttpResponse(urllib.quote(url))


@login_required
def get_s3_download_url(request):
    name = request.GET.get('name', 'noname')
    kq_id = request.GET.get('kq', 'nokq')
    url = s3_url(request.user.id, name, kq_id)
    return HttpResponse(urllib.quote(url))


def s3_url(user_id, filename, kq_id):
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    k = boto.s3.key.Key(bucket)
    name = "%d/%s/%s" % (user_id, kq_id, filename)
    k.key = name
    return k.generate_url(expires_in=0, query_auth=False)


def s3_upload(user_id, kq_id, filename, file_obj):
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    k = boto.s3.key.Key(bucket)
    name = "%d/%s/%s" % (user_id, kq_id, filename)
    k.key = name
    k.set_contents_from_file(file_obj)
    k.make_public()


@login_required
def course_review_upload(request, course_slug):
    if request.method == "POST":
        course = get_course_if_user_can_view_or_404(course_slug, request)
        file_to_upload = request.FILES.get('pr_file', None)
        submission_text = request.POST.get('pr-submission', '')

        kq = get_object_or_404(KnowledgeQuantum, id=request.POST.get('kq_id', 0))
        unit = kq.unit

        if (file_to_upload.size / (1024 * 1024) >= settings.PEER_REVIEW_FILE_MAX_SIZE):
            messages.error(request, _('Your file is greater than the max allowed size (%d MB).') % settings.PEER_REVIEW_FILE_MAX_SIZE)
            return HttpResponseRedirect(reverse('course_classroom', args=[course_slug]) + "#unit%d/kq%d/p" % (unit.id, kq.id))

        if (len(submission_text) >= settings.PEER_REVIEW_TEXT_MAX_SIZE):
            messages.error(request, _('Your text is greater than the max allowed size (%d characters).') % settings.PEER_REVIEW_TEXT_MAX_SIZE)
            return HttpResponseRedirect(reverse('course_classroom', args=[course_slug]) + "#unit%d/kq%d/p" % (unit.id, kq.id))

        s3_upload(request.user.id, kq.id, file_to_upload.name, file_to_upload)
        file_url = s3_url(request.user.id, file_to_upload.name, kq.id)
        submission = {
            "author": request.user.id,
            "author_reviews": 0,
            "text": request.POST.get('pr-submission', ''),
            "file": file_url,
            "created": datetime.utcnow(),
            "reviews": 0,
            "course": course.id,
            "unit": unit.id,
            "kq": kq.id,
        }
        insert_p2p_if_does_not_exists_or_raise(submission)
        return HttpResponseRedirect(reverse('course_classroom', args=[course_slug]) + "#unit%d/kq%d/p" % (unit.id, kq.id))

def _get_peer_review_submission(user_id, kq_id, assignation_expire, lang=None):
    collection = get_db().get_collection('peer_review_submissions')
    if lang:
        submission = collection.find({
            'kq': kq_id,
            '$or': [
                {
                    'assigned_to': {
                        '$exists': False
                    },
                },
                {
                    'assigned_when': {
                        '$lt': assignation_expire
                    },
                }
            ],
            'author': {
                '$ne': user_id
            },
            'language': lang,
            'reviewers': {
                '$ne': user_id
            }
        }).sort([
            ('reviews', pymongo.ASCENDING),
            ('author_reviews', pymongo.DESCENDING),
        ]).limit(1)
    else:
        submission = collection.find({
            'kq': kq_id,
            '$or': [
                {
                    'assigned_to': {
                        '$exists': False
                    },
                },
                {
                    'assigned_when': {
                        '$lt': assignation_expire
                    },
                }
            ],
            'author': {
                '$ne': user_id
            },
            'reviewers': {
                '$ne': user_id
            }
        }).sort([
            ('reviews', pymongo.ASCENDING),
            ('author_reviews', pymongo.DESCENDING),
        ]).limit(1)

    return submission

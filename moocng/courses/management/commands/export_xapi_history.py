# -*- coding: utf-8 -*-

import requests
import sys
import traceback
import json
import re
import time
import calendar
from optparse import make_option

import pyprind

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse

from moocng.users.models import User
from moocng.courses.models import Course, CourseStudent
from moocng.x_api.utils import learnerAccessAPage, learnerEnrollsInMooc, learnerSubmitsAResource
from moocng import mongodb

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('-b', '--datebefore',
					action='store',
					dest='datebefore',
					default='',
					help='Max date to export. Format "DD/MM/YYYY hh:mm"'),
		make_option('-a', '--dateafter',
					action='store',
					dest='dateafter',
					default='',
					help='Min date to export. Format "DD/MM/YYYY hh:mm"'),
		make_option('-e', '--enrollments',
					action='store_true',
					dest='enrollments',
					default='',
					help='Export only enrollments'),

		make_option('-c', '--accesses',
					action='store_true',
					dest='accesses',
					default='',
					help='Export only accesses'),
		make_option('-f', '--forum',
					action='store_true',
					dest='forum',
					default='',
					help='Export forum entries'),
		make_option('--debug',
					action='store_true',
					dest='debug',
					default='',
					help='Show debug messages')
	)

	def error(self, message):
		self.stderr.write("%s\n" % message.encode("ascii", "replace"))

	def message(self, message):
		self.stdout.write("%s\n" % message.encode("ascii", "replace"))

	def handle(self, *args, **options):
		if options['datebefore']:
			max_timestamp = calendar.timegm(time.strptime(options['datebefore'], '%d/%m/%Y %H:%M'))
		else:
			max_timestamp = calendar.timegm(time.gmtime())

		if options['dateafter']:
			min_timestamp = calendar.timegm(time.strptime(options['dateafter'], '%d/%m/%Y %H:%M'))
		else:
			min_timestamp = 0

		if options['enrollments'] or (not options['accesses'] and not options['forum']):
			# Get enrollments
			enrollments = CourseStudent.objects.exclude(timestamp__lte=min_timestamp).filter(timestamp__lte=max_timestamp)
			self.message("%d enrollments between %d and %d" % (enrollments.count(), min_timestamp, max_timestamp))

			#Send each enrollment entry as xAPI statement
			bar = pyprind.ProgBar(enrollments.count())
			for enrollment in enrollments:
				try:
					geolocation = {
						'lat': enrollment.pos_lat,
						'lon': enrollment.pos_lon
					}
					timestamp = time.gmtime(enrollment.timestamp)
					learnerEnrollsInMooc(enrollment.student, enrollment.course, geolocation, timestamp)
				except:
					self.error('ERROR sending an statement for user %s in enrollment with timestamp %s' % (enrollment.student, time.strftime("%d/%m/%Y %H:%M:%S", timestamp)))
					if options['debug']:
						exc_type, exc_value, exc_traceback = sys.exc_info()
						self.error('Exception %s: %s' % (exc_type, exc_value))
						traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
					continue

				bar.update()

			self.message('\nEnrollments succesfully exported')

		if options['accesses'] or (not options['enrollments'] and not options['forum']):
			# Get history
			history_col = mongodb.get_db().get_collection('history')
			histories = history_col.find({'$and': [
        									{'timestamp': {'$lte': max_timestamp * 1000} },
        									{'timestamp': {'$gte': min_timestamp * 1000} }
        								]})
			self.message("%d histories until %d" % (histories.count(), max_timestamp))

			# Send each history entry as xAPI Statement
			bar = pyprind.ProgBar(histories.count())
			for history in histories:
				course = None
				try:
					user_id = str(int(history['user_id']))
					user = User.objects.get(pk=user_id)
					if 'course_id' in history:
						course_id = str(int(history['course_id']))
						course = Course.objects.get(pk=course_id)

					page = {}
					page['url'] = history['url']
					if course:
						page['name'] = course.name
						page['description'] = course.name
					else:
						page['name'] = ''
						page['description'] = ''

					geolocation = {
						'lat': history['lat'],
						'lon': history['lon']
					}
					timestamp = time.gmtime(history['timestamp']/1000)
					learnerAccessAPage(user, page, course, geolocation, timestamp)
				except:
					self.error('ERROR sending a statement for user %s in history with timestamp %s' % (history['user_id'], time.strftime("%d/%m/%Y %H:%M:%S", timestamp)))
					if options['debug']:
						exc_type, exc_value, exc_traceback = sys.exc_info()
						self.error('Exception %s: %s' % (exc_type, exc_value))
						traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
					continue

				bar.update()

			self.message('\nHistory succesfully exported')

		if options['forum']:
			# Get forum entries
			if options['datebefore']:
				max_date = time.strftime('%Y-%m-%dT%H:%M',time.strptime(options['datebefore'], '%d/%m/%Y %H:%M'))
			else:
				max_date = time.strftime('%Y-%m-%dT%H:%M',time.gmtime())

			if options['dateafter']:
				min_date = time.strftime('%Y-%m-%dT%H:%M',time.strptime(options['dateafter'], '%d/%m/%Y %H:%M'))
			else:
				min_date = '1970-01-01T00:00'
			forum_col = mongodb.get_db().get_collection('forum_post')
			forum_posts = forum_col.find({'$and': [
        									{'date': {'$lte': max_date} },
        									{'date': {'$gte': min_date} }
        								]})
			self.message("%d forum posts between %s and %s" % (forum_posts.count(), min_date, max_date))

			# Send each post entry as xAPI Statement
			bar = pyprind.ProgBar(forum_posts.count())
			for post in forum_posts:
				course = None
				try:
					user_id = str(int(post['id_user']))
					user = User.objects.get(pk=user_id)
					if 'category_slug' in post:
						course_slug = str(post['category_slug'])
						course = Course.objects.get(slug=course_slug)

					page = {}
					post_url = "https://%s%s" % (settings.API_URI, reverse('course_forum_post', kwargs={'course_slug': course_slug, 'post_id': post['_id']})),
					page['url'] = post_url[0]

					if 'is_child' in post:
						is_child = bool(post['is_child'])
					else:
						is_child = False

					if is_child:
						page['type'] = 'threadreply'
						page['description'] = "This is a forum message"
					else:
						page['type'] = 'threadpost'
						page['description'] = "This is a thread-opening forum message"

					if 'title' in post:
						page['name'] = post['title']
					else:
						page['name'] = "Unnamed post"

					geolocation = {
						'lat': 0.0,
						'lon': 0.0
					}
					timestamp = time.strptime(post['date'], '%Y-%m-%dT%H:%M:%S.%f')
					learnerSubmitsAResource(user, page, course, geolocation, timestamp)
				except:
					self.error('\nERROR sending a statement for user %s in post with timestamp %s' % (post['id_user'], post['date']))
					if options['debug']:
						exc_type, exc_value, exc_traceback = sys.exc_info()
						self.error('Exception %s: %s' % (exc_type, exc_value))
						traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
					continue

				bar.update()

			self.message('\nForum succesfully exported')

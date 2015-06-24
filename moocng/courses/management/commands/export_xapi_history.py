# -*- coding: utf-8 -*-

import requests
import sys
import json
import re
import time
import calendar
from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from moocng.users.models import User
from moocng.courses.models import Course, CourseStudent
from moocng.x_api.utils import learnerAccessAPage, learnerEnrollsInMooc
from moocng import mongodb

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('-d', '--date',
					action='store',
					dest='date',
					default='',
					help='Max date to export. Format "DD/MM/YYYY hh:mm"'),
	)

	def error(self, message):
		self.stderr.write("%s\n" % message.encode("ascii", "replace"))

	def message(self, message):
		self.stdout.write("%s\n" % message.encode("ascii", "replace"))

	def handle(self, *args, **options):
		if options['date']:
			max_timestamp = calendar.timegm(time.strptime(options['date'], '%d/%m/%Y %H:%M'))
		else:
			max_timestamp = calendar.timegm(time.gmtime())

		# Get enrollments
		enrollments = CourseStudent.objects.filter(timestamp__lte=max_timestamp)
		print "%d enrollments until %d" % (enrollments.count(), max_timestamp)

		#Send each enrroment entry as xAPI Statement
		for enrollment in enrollments:
			geolocation = {
				'lat': enrollment.pos_lat,
				'lon': enrollment.pos_lon
			}
			learnerEnrollsInMooc(enrollment.student, enrollment.course, geolocation)
		self.message('Enrollments succesfully exported')

		# Get history
		history_col = mongodb.get_db().get_collection('history')
		histories = history_col.find({'timestamp': {'$lte': max_timestamp * 1000}})
		print "%d histories until %d" % (histories.count(), max_timestamp)

		# Send each history entry as xAPI Statement
		for history in histories:
			course = None
			try:
				user_id = str(int(history['user_id']))
				user = User.objects.get(pk=user_id)
				if 'course_id' in history:
					course_id = str(int(history['course_id']))
					course = Course.objects.get(pk=course_id)
			except (ValueError, TypeError):
				continue
			
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
			learnerAccessAPage(user, page, geolocation)

		self.message('History succesfully exported')

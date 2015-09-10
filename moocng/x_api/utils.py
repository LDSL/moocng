# -*- coding: utf-8 -*-

import requests
import sys
import json
import re
import time

from django.conf import settings
from django.contrib.auth.models import User

from moocng.courses.models import Course, KnowledgeQuantum

def _sendStatement(verb):
	try:
		print "Statement: " + json.dumps(verb)
		headers = {
			"Content-Type": "application/json",
			"X-Experience-API-Version": "1.0.0",
			"Authorization": settings.XAPI_AUTH
		}
		r = requests.post(settings.XAPI_URL, data=json.dumps(verb), headers=headers)
		if not r.status_code == requests.codes.ok:
			print "  --> Couldn't send this statement"
			print r.text

	except:
		print "  !!! Error sending statement"
		print "      Unexpected error:", sys.exc_info()

def _populateVerbAboutMOOC(user, course, geolocation, timestamp):
	verb = {
	    "actor": {
	        "objectType": "Agent",
	        "account": {
	        "homePage": "https://portal.ecolearning.eu?user=%s" % (user.get_profile().sub),
	        "name": user.get_profile().sub
	        }
	    },
	    "verb": {
	        "id": "http://activitystrea.ms/schema/1.0/access",
	        "display": {
	            "en-US": "Indicates the learner accessed the MOOC",
	        },
	    },
	    "object": {
	        "objectType": "Activity",
	        "id": 'oai:' + '.'.join(settings.API_URI.split(".")[::-1]) + ":" + str(course.id),
	        "definition": {
	            "name": {
	                "en-US": course.name,
	            },
	            "description": {
	                "en-US": course.description,
	            },
	            "type": "http://adlnet.gov/expapi/activities/course",
	        }
	    },
	    "context": {
	    	"extensions": {
	    		"http://activitystrea.ms/schema/1.0/place": {
	                "objectType": "Place",
	                "id": "http://vocab.org/placetime/geopoint/wgs84/X%sY%s.html" % (geolocation['lon'], geolocation['lat']),  # Not mandatory, Maren Scheffel asked for it
	                "geojson": {
	                    "type": "FeatureCollection",
	                    "features": [
	                        {
	                            "type": "Feature",
	                            "geometry": {
	                                "type": "Point",
	                                "coordinates": [geolocation['lon'], geolocation['lat']]
	                            }
	                        }
	                    ]
	                },
	                "definition": {
	                    "name": {
	                        "en-US": "Place"
	                    },
	                    "description": {
	                        "en-US": "Represents a physical location."
	                    },
	                    "type": "http://activitystrea.ms/schema/1.0/place"
	                }
	            }
	        }
	    },
	    "timestamp": timestamp
	}
	return verb

def _populateVerbAboutResource(user, resource, course, geolocation, timestamp, result=None):
	verb = {
	    "actor": {
	        "objectType": "Agent",
	        "account": {
	            "homePage": "https://portal.ecolearning.eu?user=%s" % (user.get_profile().sub),
	            "name": user.get_profile().sub
	        }
	    },
	    "verb": {
	        "id": resource['verb_id'],
	        "display": {
	            "en-US": resource['verb_desc']
	        }
	    },
	    "object": {
	        "objectType": "Activity",
	        "id": resource['url'],
	        "definition": {
	            "name": {
	                "en-US": resource['name']
	            },
	            "description": {
	                "en-US": resource['description']
	            },
	            "type": resource['type_id']
	        }
	    },
	    "context": {
	        "extensions": {
	            "http://activitystrea.ms/schema/1.0/place": {
	                "objectType": "Place",
	                "id": "http://vocab.org/placetime/geopoint/wgs84/X%fY%f.html" % (geolocation['lon'], geolocation['lat']), # Not mandatory, Maren Scheffel asked for it
	                "geojson": {
	                    "type": "FeatureCollection",
	                    "features": [
	                        {
	                            "type": "Feature",
	                            "geometry": {
	                                "type": "Point",
	                                "coordinates": [geolocation['lon'], geolocation['lat']]
	                            },
#	                            "properties": {
#	                                "property1": "value1" # Not mandatory, but useful to include more metadata about geolocation */
#	                            }
	                        }
	                    ]
	                },
	                "definition": {
	                    "name": {
	                        "en-US": "Place"
	                    },
	                    "description": {
	                        "en-US": "Represents a physical location."
	                    },
	                    "type": "http://activitystrea.ms/schema/1.0/place"
	                }
	            }
	        },
			"contextActivities": {
				"parent": [
					{
						"id": 'oai:' + '.'.join(settings.API_URI.split(".")[::-1]) + ":" + str(course.id),
						"objectType": "Activity",
						"definition": {
							"name": {
								"en-US": course.name
							},
							"description": {
								"en-US": course.description
							},
							"type": "http://adlnet.gov/expapi/activities/course"
						}
					}
				]
			}
		},
	    "timestamp": timestamp
	}

	if result:
		verb["result"] = {
			"score": {
				"scaled": result["score"]
			},
			"success": result["score"] >= 0.5 and True or False,
			"completion": True,
			"response": result["comment"] or ""
		}

	return verb

def learnerEnrollsInMooc(user, course, geolocation, timestamp=None):
	if not timestamp:
		timestamp = time.gmtime()
	formatted_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", timestamp)

	verb = {
		    "actor": {
		        "objectType": "Agent",
		        "account": {
		        "homePage": "https://portal.ecolearning.eu?user=%s" % (user.get_profile().sub),
		        "name": user.get_profile().sub
		        }
		    },
		    "verb": {
		        "id": "http://adlnet.gov/expapi/verbs/registered",
		        "display": {
		            "en-US": "Indicates the learner registered/enrolled for MOOC",
		        },
		    },
		    "object": {
		        "objectType": "Activity",
		        "id": 'oai:' + '.'.join(settings.API_URI.split(".")[::-1]) + ":" + str(course.id),
		        "definition": {
		            "name": {
		                "en-US": course.name,
		            },
		            "description": {
		                "en-US": course.description,
		            },
		            "type": "http://adlnet.gov/expapi/activities/course",
		        }
		    },
		    "context": {
		    	"extensions": {
		    		"http://activitystrea.ms/schema/1.0/place": {
		                "objectType": "Place",
		                "id": "http://vocab.org/placetime/geopoint/wgs84/X%sY%s.html" % (geolocation['lon'], geolocation['lat']),  # Not mandatory, Maren Scheffel asked for it
		                "geojson": {
		                    "type": "FeatureCollection",
		                    "features": [
		                        {
		                            "type": "Feature",
		                            "geometry": {
		                                "type": "Point",
		                                "coordinates": [geolocation['lon'], geolocation['lat']]
		                            },
#		                            "properties": {
#		                                "property1": "value1"  # Not mandatory, but useful to include more metadata about geolocation
#		                            }
		                        }
		                    ]
		                },
		                "definition": {
		                    "name": {
		                        "en-US": "Place"
		                    },
		                    "description": {
		                        "en-US": "Represents a physical location."
		                    },
		                    "type": "http://activitystrea.ms/schema/1.0/place"
		                }
		            }
		        }
		    },
		    "timestamp": formatted_timestamp
		}
	_sendStatement(verb)

def learnerAccessAPage(user, resource, course, geolocation, timestamp=None):
	resource_types = {
		"mooc": "http://adlnet.gov/expapi/activities/course",
		"page": "http://activitystrea.ms/schema/1.0/page",
		"syllabus": "http://www.ecolearning.eu/expapi/activitytype/syllabus",
		"task": "http://activitystrea.ms/schema/1.0/task",
		"assessment": "http://adlnet.gov/expapi/activities/assessment",
		"peerassessment": "http://www.ecolearning.eu/expapi/activitytype/peerassessment",
		"activitystream": "http://www.ecolearning.eu/expapi/activitytype/activitystream",
		"forum": "http://id.tincanapi.com/activitytype/discussion",
		"kq_book": "http://id.tincanapi.com/activitytype/book",
		"kq_video": "http://activitystrea.ms/schema/1.0/video",
		"kq_presentation": "http://id.tincanapi.com/activitytype/slide-deck"
	}
	resource_verbs = {
		"mooc": "Indicates the learner accessed the MOOC",
		"page": "Indicates the learner accessed a page",
		"syllabus": "Indicates the learner accessed a syllabus",
		"task": "Indicates the learner accessed a task",
		"assessment": "Indicates the learner accessed an assessment",
		"peerassessment": "Indicates the learner accessed a peer assessment",
		"activitystream": "Indicates the learner accessed an activity stream",
		"forum": "Indicates the learner accessed a forum",
		"kq_book": "Indicates the learner accessed a book",
		"kq_video": "Indicates the learner accessed a video",
		"kq_presentation": "Indicates the learner accessed a slidedeck"
	}

	resource_type = "page"
	if re.search('\/syllabus', resource['url']):
		resource_type = "syllabus"
	elif re.search('\/classroom\/', resource['url']):
		if re.search('\/classroom\/.*\/kq[0-9]+\/q', resource['url']):
			resource_type = "task"
		elif re.search('\/classroom\/#unit[0-9]+\/kq[0-9]+\/p', resource['url']):
				resource_type = "assessment"
		elif re.search('\/classroom\/#unit[0-9]+\/kq[0-9]+\/a', resource['url']):
			resource_type = "page"
		elif re.search('\/classroom\/#unit[0-9]+\/kq[0-9]+$', resource['url']):
			resource_type = "kq"
			res = re.search('\/classroom\/#unit[0-9]+\/kq(?P<kqid>[0-9]+)$', resource['url'])
			kq = KnowledgeQuantum.objects.get(pk=res.group('kqid'))
			media_types = {elem['id']: elem['type'] for elem in settings.MEDIA_CONTENT_TYPES}
			resource_type = "kq_%s" % (media_types[kq.media_content_type])
	elif re.search('\/user\/posts\/hashtag\/', resource['url']):
		resource_type = "activitystream"
	elif re.search('\/course\/.*\/forum\/', resource['url']):
		resource_type = "forum"
	elif re.search('\/course\/.*\/reviews\/[0-9]+\/review\/', resource['url']):
		resource_type = "peerassessment"
	elif re.search('\/course\/[a-zA-Z0-9-_]+\/$', resource['url']):
		resource_type = "mooc"

	if not timestamp:
		timestamp = time.gmtime()
	formatted_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", timestamp)

	if resource_type != "mooc":
		resource['verb_id'] = "http://activitystrea.ms/schema/1.0/access"
		resource['verb_desc'] = resource_verbs[resource_type]
		resource['type_id'] = resource_types[resource_type]
		verb = _populateVerbAboutResource(user, resource, course, geolocation, formatted_timestamp)
	else:
		verb = _populateVerbAboutMOOC(user, course, geolocation, formatted_timestamp)

	_sendStatement(verb)

def learnerSubmitsAResource(user, resource, course, geolocation, timestamp=None, result=None):
	resource_types = {
		"task": "http://activitystrea.ms/schema/1.0/task",
		"assessment": "http://adlnet.gov/expapi/activities/assessment",
		"peerfeedback": "http://www.ecolearning.eu/expapi/activitytype/peerfeedback",
	}
	resource_verbs = {
		"task": "Indicates the learner submitted a task",
		"assessment": "Indicates the learner submitted an assessment",
		"peerfeedback": "Indicates the learner submitted a peer feedback",
	}

	if not timestamp:
		timestamp = time.gmtime()
	formatted_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", timestamp)

	resource['verb_id'] = "http://activitystrea.ms/schema/1.0/submit"
	resource['verb_desc'] = resource_verbs[resource['type']]
	resource['type_id'] = resource_types[resource['type']]
	verb = _populateVerbAboutResource(user, resource, course, geolocation, formatted_timestamp, result)

	_sendStatement(verb)

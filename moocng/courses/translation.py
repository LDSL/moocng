from modeltranslation.translator import translator, TranslationOptions
from moocng.courses.models import Course

class CourseTranslationOptions(TranslationOptions):
	fields = ('name', 'description', 'requirements', 'learning_goals', 'estimated_effort')

translator.register(Course, CourseTranslationOptions)
from modeltranslation.translator import translator, TranslationOptions
from moocng.courses.models import Course, StaticPage

class CourseTranslationOptions(TranslationOptions):
	fields = ('name', 'description', 'requirements', 'learning_goals', 'estimated_effort')

class StaticPageTranslationOptions(TranslationOptions):
	fields = ('title', 'body')

translator.register(Course, CourseTranslationOptions)
translator.register(StaticPage, StaticPageTranslationOptions)
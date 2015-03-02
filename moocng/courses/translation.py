from modeltranslation.translator import translator, TranslationOptions
from moocng.courses.models import Course, StaticPage, Unit, KnowledgeQuantum, Question, Option

class CourseTranslationOptions(TranslationOptions):
	fields = ('name', 'description', 'requirements', 'learning_goals', 'estimated_effort')

class StaticPageTranslationOptions(TranslationOptions):
	fields = ('title', 'body')

class UnitTranslationOptions(TranslationOptions):
	fields = ('title',)

class KnowledgeQuantumTranslationOptions(TranslationOptions):
	fields = ('title', 'teacher_comments', 'supplementary_material')

class QuestionTranslationOptions(TranslationOptions):
	fields = ('solution_text',)

class OptionTranslationOptions(TranslationOptions):
	fields = ('solution', 'text', 'feedback')

translator.register(Course, CourseTranslationOptions)
translator.register(StaticPage, StaticPageTranslationOptions)
translator.register(Unit, UnitTranslationOptions)
translator.register(KnowledgeQuantum, KnowledgeQuantumTranslationOptions)
translator.register(Question, QuestionTranslationOptions)
translator.register(Option, OptionTranslationOptions)
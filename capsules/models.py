from django.db import models
from accounts.models import User
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.base import TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
import numpy as np
from django.core.exceptions import ValidationError

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.pk is None and Category.objects.count() >= 7:
            raise ValidationError('Cannot create more than 7 categories')
        super().save(*args, **kwargs)

nlp = spacy.load('en_core_web_sm')

X_train = [
    'mindfulness joy appreciating thankful meditation peace calm',
    'engage key unlocking potential live growth learning development',
    'creativity innovation art imagination design thinking originality',
    'motivation inspiration drive ambition determination perseverance resilience',
    'relationship love friendship family connection bonding companionship',
    'wellness health fitness wellbeing nutrition exercise sleep',
]
y_train = [
    'Mindfulness',
    'Personal Growth',
    'Creativity',
    'Motivation',
    'Relationships',
    'Wellness',
]

le = LabelEncoder()
y_train = le.fit_transform(y_train)

class TextToVectorTransformer(TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([nlp(text).vector for text in X])

pipeline = Pipeline([
    ('vect', TextToVectorTransformer()),
    ('clf', LinearSVC(dual=True)),
])

pipeline.fit(X_train, y_train)

class Capsule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag)
    categories = models.ManyToManyField(Category)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.determine_categories()

    def determine_categories(self):
        # tags = ' '.join(tag.name for tag in self.tags.all())
        # categories = pipeline.predict([tags])
        categories = pipeline.predict([self.content])
        categories = le.inverse_transform(categories)
        if len(categories) == 0:
            categories = ['Others']
        elif len(categories) > 3:
            categories = categories[:3]
        
        category_instances = [Category.objects.get_or_create(name=category)[0] for category in categories]
        self.categories.set(category_instances)
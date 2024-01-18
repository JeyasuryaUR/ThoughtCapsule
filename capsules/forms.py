from django import forms
from .models import Capsule, Tag
import re

class CapsuleForm(forms.ModelForm):
    tags = forms.CharField()

    class Meta:
        model = Capsule
        fields = ['content', 'tags']

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        tag_list = [Tag.objects.get_or_create(name=name.strip().lower())[0] for name in re.split(',\s*', tags) if name.strip() and name.strip() != '']
        return tag_list
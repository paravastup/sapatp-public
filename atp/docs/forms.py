from django import forms

from .models import Doc


class DocForm(forms.ModelForm):

    class Meta:
        model = Doc
        fields = ('author','title', 'text',)

        widgets = {
            'title': forms.TextInput(attrs={'class': 'textinputclass'}),
            'text': forms.Textarea(attrs={'class': 'editable medium-editor-textarea doccontent'}),
        }

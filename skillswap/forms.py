from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Feedback, Match, Profile, Request, Skill, UserSkill

User = get_user_model()


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget,
                          (
                                  forms.TextInput,
                                  forms.EmailInput,
                                  forms.PasswordInput,
                                  forms.Textarea,
                                  forms.Select,
                                  forms.FileInput,
                          )):
                field.widget.attrs.setdefault('class', 'form-control')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class BootstrapAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'availability', 'preferred_mode', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class SkillForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Skill
        fields = ('name', 'category', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class UserSkillForm(BootstrapFormMixin, forms.ModelForm):
    skill_name = forms.CharField(required=False, label='New skill name')
    skill_category = forms.CharField(required=False, label='New skill category')
    skill_description = forms.CharField(
        required=False,
        label='New skill description',
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = UserSkill
        fields = ('skill', 'type', 'level')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields['skill'].required = False

    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get('skill')
        skill_name = cleaned_data.get('skill_name')
        skill_category = cleaned_data.get('skill_category')

        if not skill and not (skill_name and skill_category):
            raise forms.ValidationError('Select an existing skill or add a new one.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        skill_name = self.cleaned_data.get('skill_name')
        skill_category = self.cleaned_data.get('skill_category')
        skill_description = self.cleaned_data.get('skill_description')

        if skill_name and skill_category:
            skill, _ = Skill.objects.get_or_create(
                name=skill_name.strip(),
                category=skill_category.strip(),
                defaults={'description': skill_description or ''},
            )
            instance.skill = skill

        if commit:
            instance.save()
        return instance


class RequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Request
        fields = ('skill', 'title', 'description', 'preferred_time', 'status')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class MatchInviteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Match
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class FeedbackForm(BootstrapFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(value, value) for value in range(1, 6)],
        coerce=int,
        widget=forms.Select,
    )

    class Meta:
        model = Feedback
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'maxlength': 300}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

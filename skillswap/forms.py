from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Feedback, Match, Message, Profile, Report, Request, Skill, UserSkill

User = get_user_model()


class BootstrapFormMixin:
    # Add Bootstrap classes to common form widgets
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
    # Require email during registration
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class BootstrapAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    # Login form with Bootstrap styling
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'availability', 'preferred_mode', 'location')
        widgets = {
            # Make bio easier to type with a bigger text area
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
    # Extra fields so user can add a new skill if it does not already exist
    skill_name = forms.CharField(required=False, label='New skill name')
    skill_category = forms.CharField(required=False, label='New skill category')
    skill_description = forms.CharField(
        required=False,
        label='New skill description',
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = UserSkill
        fields = ('skill', 'type', 'level', 'learning_months', 'self_rating')
        help_texts = {
            'learning_months': 'Optional. Total months spent learning or practicing.',
            'self_rating': 'Optional. Rate your confidence from 1 (low) to 5 (high).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        # Existing skill is optional because user may create a new one
        self.fields['skill'].required = False

    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get('skill')
        skill_name = cleaned_data.get('skill_name')
        skill_category = cleaned_data.get('skill_category')

        # User must either choose a skill or enter a new one
        if not skill and not (skill_name and skill_category):
            raise forms.ValidationError('Select an existing skill or add a new one.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        skill_name = self.cleaned_data.get('skill_name')
        skill_category = self.cleaned_data.get('skill_category')
        skill_description = self.cleaned_data.get('skill_description')

        # Create the skill if user entered a new one
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
    # Use dropdown choices for rating from 1 to 5
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


class MessageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ('body',)
        widgets = {
            # Message input box in chat
            'body': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'details')
        widgets = {
            'details': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
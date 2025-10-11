
from django import forms
from .models import EmailTemplate
from catalog.models import Platform, TrackingParamSet, OfferLink
from django_select2.forms import ModelSelect2Widget
from django import forms
from .models import EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = [
            "title",
            "subject",
            "from_name",
            "body_html",
            "body_text",
            "is_public",
            "snapshot",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter template title"
            }),
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email subject"
            }),
            "from_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Sender name"
            }),
            "body_html": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": "Use {{placeholders}} for personalization"
            }),
            "body_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Plain text version (optional)"
            }),
            "is_public": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "snapshot": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }

    def clean_body_html(self):
        """Ensure body_html is not empty."""
        body_html = self.cleaned_data.get("body_html", "").strip()
        if not body_html:
            raise forms.ValidationError("Body HTML cannot be empty.")
        return body_html


class UseTemplateForm(forms.Form):
    platform = forms.ModelChoiceField(queryset=Platform.objects.none(), required=False)
    offer_link = forms.ModelChoiceField(
        queryset=OfferLink.objects.none(),
        required=False,
        widget=ModelSelect2Widget(
            model=OfferLink,
            search_fields=['offer__name__icontains'],
            data_view='emails:offerlink-autocomplete',  # important!
            attrs={'data-placeholder': 'Type to search…'}
        )
    )
    cta_fallback_url = forms.URLField(required=False, help_text="Used if no Offer Link selected")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['platform'].queryset = Platform.objects.filter(created_by=user)
        self.fields['offer_link'].queryset = OfferLink.objects.filter(is_active=True)
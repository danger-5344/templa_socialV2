
from django import forms
from .models import Platform, TrackingParamSet
import json
from .models import Offer, OfferLink, OfferNetwork as Network, PersonalizedTag

class PlatformForm(forms.ModelForm):
    class Meta:
        model = Platform
        fields = ["name"]

class TrackingParamSetForm(forms.ModelForm):
    class Meta:
        model = TrackingParamSet
        fields = ['platform', 'params', 'is_active']
        widgets = {
            'params': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"utm_source":"newsletter"}'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # ✅ safely remove `user` from kwargs
        super().__init__(*args, **kwargs)

        if user:
            # show only platforms created by this user
            self.fields["platform"].queryset = Platform.objects.filter(created_by=user)
        
class OfferLinkWithOfferForm(forms.ModelForm):
    offer_name = forms.CharField(max_length=200, label="Offer Name")
    network = forms.ModelChoiceField(queryset=Network.objects.all(), label="Network")

    class Meta:
        model = OfferLink
        fields = ["network", "offer_name", "url", "is_active"]

class PersonalizedTagForm(forms.ModelForm):
    class Meta:
        model = PersonalizedTag
        fields = [
            "platform",
            "first_name_tag",
            "last_name_tag",
            "email_tag",
            "date_tag",
            "footer1_code",
            "footer2_code",
            "is_active",
        ]
        widgets = {
            "platform": forms.Select(attrs={"class": "input"}),
            "first_name_tag": forms.TextInput(attrs={"placeholder": "{{first_name}}"}),
            "last_name_tag": forms.TextInput(attrs={"placeholder": "{{last_name}}"}),
            "email_tag": forms.TextInput(attrs={"placeholder": "{{email}}"}),
            "date_tag": forms.TextInput(attrs={"placeholder": "{{date}}"}),
            "footer1_code": forms.Textarea(attrs={"rows":3}),
            "footer2_code": forms.Textarea(attrs={"rows":3}),
        }
        help_texts = {
            "footer1_code": "HTML or text fragment that will be appended in footer 1.",
            "footer2_code": "HTML or text fragment that will be appended in footer 2.",
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # ✅ safely remove `user` from kwargs
        super().__init__(*args, **kwargs)

        if user:
            # show only platforms created by this user
            self.fields["platform"].queryset = Platform.objects.filter(created_by=user)

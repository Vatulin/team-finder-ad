from urllib.parse import urlsplit

from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if not url:
            return ""

        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"github.com", "www.github.com"}
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise forms.ValidationError(
                "Укажите ссылку на github.com."
            )

        return url
from calendar import day_name

from django import forms

from .models import Chore

WEEKDAY_CHOICES = [(i + 1, day_name[i]) for i in range(7)]


class ChoreForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Used when recurrence is Weekly.",
    )
    recurrence = forms.TypedChoiceField(
        choices=Chore.Recurrence.choices,
        required=False,
        empty_value=Chore.Recurrence.NONE,
    )

    class Meta:
        model = Chore
        fields = ["name", "due_date", "recurrence"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        recurrence = cleaned.get("recurrence")
        due_date = cleaned.get("due_date")
        weekdays = cleaned.get("weekdays")

        if recurrence in (Chore.Recurrence.DAILY, Chore.Recurrence.WEEKLY):
            if not due_date:
                self.add_error("due_date", "A recurring chore requires a due date.")
            if recurrence == Chore.Recurrence.WEEKLY and not weekdays:
                self.add_error(
                    "weekdays", "Weekly chores require at least one weekday."
                )
        return cleaned

    def save(self, commit=True):
        chore = super().save(commit=False)
        chore.weekdays = ",".join(str(w) for w in sorted(self.cleaned_data.get("weekdays") or []))
        if commit:
            chore.save()
        return chore

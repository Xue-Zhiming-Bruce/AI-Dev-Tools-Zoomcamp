from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ChoreForm
from .models import Chore


def index(request):
    if request.method == "POST":
        form = ChoreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")
    else:
        form = ChoreForm()
    chores = Chore.objects.filter(done=False).order_by("created_at")
    return render(request, "chore/index.html", {"chores": chores, "form": form})


@require_POST
def mark_done(request, chore_id):
    chore = get_object_or_404(Chore, pk=chore_id)
    chore.complete()
    return redirect("index")


SNOOZE_DAYS = {"tomorrow": 1, "next-week": 7}


@require_POST
def snooze(request, chore_id, delta):
    chore = get_object_or_404(Chore, pk=chore_id)
    if delta not in SNOOZE_DAYS:
        return HttpResponseBadRequest("unknown snooze option")
    try:
        chore.snooze(SNOOZE_DAYS[delta])
    except ValueError:
        return HttpResponseBadRequest("cannot snooze a chore without a due date")
    return redirect("index")

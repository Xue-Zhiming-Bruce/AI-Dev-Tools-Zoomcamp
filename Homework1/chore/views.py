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

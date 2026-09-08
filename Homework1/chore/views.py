from django.shortcuts import redirect, render

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
    chores = Chore.objects.order_by("created_at")
    return render(request, "chore/index.html", {"chores": chores, "form": form})

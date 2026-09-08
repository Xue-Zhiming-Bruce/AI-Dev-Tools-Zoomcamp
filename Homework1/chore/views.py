from django.shortcuts import render


def index(request):
    return render(request, "chore/index.html", {"chores": []})

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("chore/<int:chore_id>/done/", views.mark_done, name="mark_done"),
]

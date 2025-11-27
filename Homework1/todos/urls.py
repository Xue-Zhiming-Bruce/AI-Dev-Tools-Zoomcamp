from django.urls import path
from .views import (
    TodoListView,
    TodoCreateView,
    TodoUpdateView,
    TodoDeleteView,
    toggle_resolved,
)

app_name = "todos"

urlpatterns = [
    path("", TodoListView.as_view(), name="list"),
    path("create/", TodoCreateView.as_view(), name="create"),
    path("edit/<int:pk>/", TodoUpdateView.as_view(), name="edit"),
    path("delete/<int:pk>/", TodoDeleteView.as_view(), name="delete"),
    path("resolve/<int:pk>/", toggle_resolved, name="resolve"),
]


from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Todo
from .forms import TodoCreateForm, TodoUpdateForm


class TodoListView(ListView):
    model = Todo
    template_name = "todos/todo_list.html"
    context_object_name = "todos"
    ordering = ["is_resolved", "due_date", "-created_at"]


class TodoCreateView(CreateView):
    model = Todo
    form_class = TodoCreateForm
    template_name = "todos/todo_form.html"
    success_url = reverse_lazy("todos:list")


class TodoUpdateView(UpdateView):
    model = Todo
    form_class = TodoUpdateForm
    template_name = "todos/todo_form.html"
    success_url = reverse_lazy("todos:list")


class TodoDeleteView(DeleteView):
    model = Todo
    template_name = "todos/todo_confirm_delete.html"
    success_url = reverse_lazy("todos:list")


def toggle_resolved(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_resolved = not todo.is_resolved
    todo.save(update_fields=["is_resolved"]) 
    return redirect("todos:list")

# Create your views here.

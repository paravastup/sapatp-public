from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from docs.models import Doc
from django.utils import timezone
from docs.forms import DocForm

from django.views.generic import (TemplateView,ListView,
                                  DetailView,CreateView,
                                  UpdateView,DeleteView)

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


class DocListView(LoginRequiredMixin,ListView):
    login_url='/atp/login/'
    model = Doc
    template_name = 'docs/doc_list.html'
    #paginate_by=4

    def get_queryset(self):
        return Doc.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

class DocDetailView(DetailView):
    model = Doc


class CreateDocView(LoginRequiredMixin,CreateView):
    login_url = '/login/'
    redirect_field_name = 'docs/doc_detail.html'

    form_class = DocForm

    model = Doc


class DocUpdateView(LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    redirect_field_name = 'docs/doc_detail.html'

    form_class = DocForm

    model = Doc


class DraftListView(LoginRequiredMixin,ListView):
    login_url = '/login/'
    redirect_field_name = 'docs/doc_list.html'

    model = Doc

    def get_queryset(self):
        return Doc.objects.filter(published_date__isnull=True).order_by('created_date')


class DocDeleteView(LoginRequiredMixin,DeleteView):
    model = Doc
    success_url = reverse_lazy('docs:help')

#######################################
## Functions that require a pk match ##
#######################################

@login_required
def doc_publish(request, pk):
    doc = get_object_or_404(Doc, pk=pk)
    doc.publish()
    return redirect('docs:doc_detail', pk=pk)

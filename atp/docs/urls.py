from django.conf.urls import url
from . import views

app_name='docs'
urlpatterns = [
    url(r'^$',views.DocListView.as_view(),name='help'),
    url(r'^docs/(?P<pk>\d+)$', views.DocDetailView.as_view(), name='doc_detail'),
    url(r'^docs/new/$', views.CreateDocView.as_view(), name='doc_new'),
    url(r'^docs/(?P<pk>\d+)/edit/$', views.DocUpdateView.as_view(), name='doc_edit'),
    url(r'^docs/drafts/$', views.DraftListView.as_view(), name='doc_draft_list'),
    url(r'^docs/(?P<pk>\d+)/remove/$', views.DocDeleteView.as_view(), name='doc_remove'),
    url(r'^docs/(?P<pk>\d+)/publish/$', views.doc_publish, name='doc_publish'),
]

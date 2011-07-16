import shutil
import os, errno
import hashlib
import tempfile
import math
import urllib
import urllib2

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, QueryDict
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import Context, RequestContext, loader
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponseRedirect
from django.contrib import messages

from astrometry.net.models import *
from astrometry.net import settings
from astrometry.net.log import *
from astrometry.net.tmpfile import *

from astrometry.util.run_command import run_command

from astrometry.net.views.comment import *
from astrometry.net.util import *


def album(req, album_id=None):
    album = get_object_or_404(Album, pk=album_id)
    comment_form = PartialCommentForm()

    page_number = req.GET.get('page',1)
    page = get_page(album.user_images.all(),4*3,page_number)
    context = {
        'album': album,
        'comment_form': comment_form,
        'image_page': page,
        'request': req,
    }

    if album.is_public() or (album.user == req.user and req.user.is_authenticated()):
        template = 'album/view.html'
    elif SharedHideable.objects.filter(shared_with=req.user.id, hideable=album).count():
        template = 'album/view.html'
    else:
        messages.error(req, "Sorry, you don't have permission to view this content")
        template = 'album/permission_denied.html'
    return render_to_response(template, context,
        context_instance = RequestContext(req))

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        include = ('title', 'description', 'publicly_visible')
        widgets = {
            'description': forms.Textarea(attrs={'cols':60,'rows':3}),
            'publicly_visible': forms.RadioSelect(renderer=NoBulletsRenderer)
        }

@login_required
def new(req):
    if req.method == 'POST':
        form = AlbumForm(req.POST)
        title = req.POST.get('title','')
        description = req.POST.get('description','')
        publicly_visible = req.POST.get('publicly_visible','y')
        album,created = Album.objects.get_or_create(user=req.user, title=title,
                                            defaults=dict(description=description,
                                                          publicly_visible=publicly_visible))
        redirect_url = reverse('astrometry.net.views.album.album', kwargs={'album_id':album.id})
        return HttpResponseRedirect(redirect_url)
    else:
        pass

@login_required
def delete(req, album_id):
    album = get_object_or_404(Album, pk=album_id)
    redirect_url = req.GET.get('next','/')
    if album.user == req.user:
        album.delete()
        return HttpResponseRedirect(redirect_url)
    else:
        # render_to_response a "you don't have permission" view
        pass

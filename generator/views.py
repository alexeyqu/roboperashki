from django.shortcuts import render
from .perashki_generator import make_random_perashok

from .models import Perashok

def index(request):
    context = {}
    if "more" in request.POST:
        generated_text = make_random_perashok()
        context['perashok_lines'] = generated_text.split('\n')
        
    return render(request, 'index.html', context)

def perashki_list(request):
    context = []
    return render(request, 'gallery.html', context)

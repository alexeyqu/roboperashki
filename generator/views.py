from django.shortcuts import render
from .perashki_generator import make_random_perashok
from datetime import datetime

from .models import Perashok

def index(request):
    context = {}
    if "more" in request.POST:
        generated_text = make_random_perashok()
        context['perashok_lines'] = generated_text.split('\n')
        context['perashok_text'] = generated_text
    elif "save" in request.POST:
        text = request.POST['hidden_text']
        
        perashok = Perashok(perashok_text=text, adding_date=datetime.now())
        perashok.save()
        
        context['perashok_lines'] = text.split('\n')
        context['perashok_text'] = text
        context['info_message'] = "Трям! Пирожок успешно добавлен в галерею, потомки вас не забудут"
        
    return render(request, 'index.html', context)

def gallery(request):
    perashki = [[p.perashok_text.split('\n'), p.adding_date] for p in Perashok.objects.all()]
    context = {"perashki_list": perashki}
    return render(request, 'gallery.html', context)

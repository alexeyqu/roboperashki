from django.shortcuts import render
from django.conf import settings

from .collocations_counter import CollocationCounter

def collocations(request):
    context = {'pos_tags': settings.ALLOWED_POS_TAGS}
    if 'left_pos' in request.POST and 'right_pos' in request.POST:
        counter = CollocationCounter(pos_pair_list=[(request.POST['left_pos'], request.POST['right_pos'])])
        context['collocation_list'] = counter.get_k_best_collocations()
    return render(request, 'collocations_list.html', context)

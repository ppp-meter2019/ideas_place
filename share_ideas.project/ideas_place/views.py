from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.sites.shortcuts import get_current_site
import requests
import json


# Create your views here.


class UserActivation(TemplateView):
    template_name = 'front/show_message.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        try:
            message = self.activate(uidb64=self.kwargs['uidb64'], token=self.kwargs['token'])

        except Exception as e:
            message = "Unexpected {} error".format(e)
        context['message_to_show'] = message
        return self.render_to_response(context)

    def activate(self, uidb64=None, token=None, *args, **kwargs):
        """
        Return result message. Success - user mail was confirmed and users 'is_active'
        has become True, detail: - in the other case, which means user activation failed.
        """
        url = 'http://' + get_current_site(self.request).domain + reverse('rest_api:user-activate')
        data = {'activation': {"uid": uidb64, 'token': token}}
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        rq = requests.post(url, data=json.dumps(data), headers=headers)
        message = rq.json().get('success', None)

        return message if message is not None else rq.json().get('detail', None)

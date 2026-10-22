from django.contrib import messages
from django.core.exceptions import RequestDataTooBig
from django.shortcuts import redirect


class TeleversementTropGrosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, RequestDataTooBig):
            return None
        messages.error(request, "Le fichier dépasse la taille maximale.")
        return redirect(request.path)

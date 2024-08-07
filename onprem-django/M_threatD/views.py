# django
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect

# local
from .src.rule.elasticsearch_rule import RuleSet


@method_decorator(login_required, name="dispatch")
class RuleView(View):
    def get(self, request, resource_type=None, system=None):
        ruleset = RuleSet(system=system)
        context = {
            'system': system,
            'custom_ruleset': ruleset.get_ruleset_list(rule_type='custom'),
            'default_ruleset': ruleset.get_ruleset_list(rule_type='default')
        }
        return render(request, 'M_threatD/rules/elasticsearch/rule.html', context=context)

    def post(self, request, resource_type=None, system=None, action_type=None):
        try:
            ruleset = RuleSet(system=system)
            return HttpResponse(getattr(ruleset, action_type)(request=request))
        except Exception as e:
            # logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse('Wrong Request. Please Try Again.', status=400)



from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from TeirenSIEM import risk
import TeirenSIEM.log as log


###################################################################

# Topbar Alert
def topbar_alert(request):
    context = risk.alert.alert.check_topbar_alert()
    return JsonResponse(context)

###################################################################

# Log Management
## Help Modal
def log_help(request):
    return render(request, "log/help.html")

## Detail Modal
def log_modal(request, type):
    if request.method == 'POST':
        if type == 'help':
            return render(request, "log/help.html")
        elif type == 'details':
            if request.POST['cloud'] == 'Aws':
                context = log.log.get_log_detail_modal(dict(request.POST.items()))
            return render(request, "log/detail_modal.html", context)

###################################################################

# Risk Management
## Rule Details Modal
def rule_details(request, type):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = {type: risk.rule.default.get_rule_details(dict(request.POST.items()), type)}
        return render(request, f"risk/rules/{type}/details.html", context)

#############################################

### Rule Edit
## Rule Edit Modal
def rule_edit_modal(request, type):
    if request.method == 'POST':
        context = dict(request.POST.items())
        context.update(risk.rule.edit.get_edit_rule_page(context))
        context.update({'log_properties': risk.rule.add.get_log_properties(context)})
        return render(request, "risk/rules/custom/edit.html", context)
## Rule Edit Action
def edit_rule(request):
    if request.method == 'POST':
        context = risk.rule.edit.edit_rule(dict(request.POST.items()))
        return HttpResponse(context)
## Rule Edit Default Rule (Add Action Slot)
def edit_rule_add_action(request):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = risk.rule.edit.edit_rule_add_action(dict(request.POST.items()))
        return render(request, "risk/rules/custom/edit/add_action.html", context)

def edit_add_log_property(request):
    if request.method == 'POST':
        context = dict(request.POST.items())
        context.update({'log_properties': risk.rule.add.get_log_properties(context)})
        return render(request, "risk/rules/custom/edit/property_slot.html", context)

#############################################

### Rule Delete
## Rule Delete Action
def delete_rule(request):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = risk.rule.delete.delete_rule(dict(request.POST.items()))
        return HttpResponse(context)

#############################################

### Rule Add
## Rule Add Modal
def rule_add_modal(request, type):
    if request.method == 'POST':
        context = dict(request.POST.items())
        return render(request, 'risk/rules/custom/add.html', context)

## Rule Add Modal Section
def add_rule_section(request, type):
    if request.method == 'POST':
        context = dict(request.POST.items())
        context.update({'log_properties': risk.rule.add.get_log_properties(context)})
        if 'flow' in type:
            if type == 'flow_check':
                flow_check = risk.rule.add.get_flow_check(context)
                if isinstance(flow_check, str):
                    return HttpResponse(flow_check)
                context.update(flow_check)
            else:
                context.update(risk.rule.add.get_flow_slot(context))
            return render(request, "risk/rules/custom/add/flow_slot.html", context)
        else:
            if context:
                if context['cloud'] == 'Aws':
                    return render(request, f'risk/rules/custom/add/{type}.html', context)
            else:
                return render(request, f'risk/rules/custom/add/{type}.html')

## Rule Add Action
def add_rule(request):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = risk.rule.add.add_rule(dict(request.POST.items()))
        return HttpResponse(context)

#############################################

## Rule On_off
def on_off(request, type):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = risk.rule.default.rule_on_off(dict(request.POST.items()))
        return HttpResponse(context)

#############################################
## Visuals User Details Modal
def user_details(request):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = dict(request.POST.items())
            context.update(risk.visual.user.user.user_graph(context))
            return render(request, 'risk/visuals/user/details.html', context)
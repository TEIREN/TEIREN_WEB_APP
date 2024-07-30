# local class
from .src.rule.add import Add
from .src.rule.delete import Delete
from .src.rule.default import Default
from .src.rule.edit import Edit

# django
from django.shortcuts import render, redirect, HttpResponse
# Risk Management

## Rule Details Modal
def rule_details(request, resourceType, logType, ruleType):
    if request.method == 'POST':
        with Default(request) as __default:
            context = {ruleType: __default.get_rule_details(ruleType=ruleType)}
        return render(request, f"M_threatD/rules/{ruleType}/details.html", context)

# #############################################

### Rule Edit
## Rule Edit Modal
def rule_edit_modal(request, resourceType, logType):
    if request.method == 'POST':
        context = dict(request.POST.items())
        with Edit(request) as __edit:
            context.update(__edit.get_edit_rule_page())
        with Add(request) as __add:
            context.update({'log_properties':__add.get_log_properties()})
        return render(request, "M_threatD/rules/custom/edit.html", context)

## Rule Edit Action
def edit_rule(request):
    if request.method == 'POST':
        with Edit(request) as __edit:
            context = __edit.edit_rule()
        return HttpResponse(context)

# #############################################

### Rule Delete
## Rule Delete Action
def delete_rule(request):
    if request.method == 'POST':
        with Delete(request) as __delete:
            context = __delete.delete_rule()
        return HttpResponse(context)

# #############################################

### Rule Add
## Rule Add Modal
def rule_add_modal(request, resourceType, logType):
    if request.method == 'POST':
        context = dict(request.POST.items())
        return render(request, 'M_threatD/rules/custom/add.html', context)

## Rule Add Modal Section
def add_rule_section(request, section):
    if request.method == 'POST':
        context = dict(request.POST.items())
        with Add(request) as __add:
            context.update({'log_properties': __add.get_log_properties()})
        if 'flow' in section:
            if section == 'flow_check':
                flow_check = __add.get_flow_check()
                if isinstance(flow_check, str):
                    return HttpResponse(flow_check)
                context.update(flow_check)
            else:
                context.update(__add.get_flow_slot())
            return render(request, "M_threatD/rules/custom/add/flow_slot.html", context)
        else:
            if context:
                return render(request, f'M_threatD/rules/custom/add/{section}.html', context)
            else:
                return render(request, f'M_threatD/rules/custom/add/{section}.html')

## Rule Add Action
def add_rule(request):
    if request.method == 'POST':
        with Add(request) as __add:
            context = __add.add_rule()
        return HttpResponse(context)

# #############################################

## Rule On_off
def on_off(request, resourceType, logType):
    if request.method == 'POST':
        with Default(request) as __default:
            context = __default.rule_on_off()
        return HttpResponse(context)

# #############################################
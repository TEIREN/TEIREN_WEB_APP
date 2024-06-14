from django.urls import path
from .src import tests
from .src.finevo import integration, log, dashboard, tableProperty

urlpatterns = [
    path('', tests.main_test),
    path('ajax/', tests.test_ajax),
    path('dashboard/', dashboard.dashboard),
    path('trigger/', tests.running_trigger),
    path('trigger/trigger/', tests.trigger, name='trigger'),
    path('cloudformation/', tests.cloudformation, name='cloudformation'),
    path('createIamPolicy/', tests.create_iam_policy, name='createIamPolicy'),
    path('login/', tests.login_, name='login'),
    path('register/', tests.register_, name='register'),
    path('log/<system>/', log.list_logs, name='list_logs'),  # log.py list_logs()
    path('log/<system>/property/save/', tableProperty.save_table_property, name='save_property'),  # tableProperty.py save_table_property()
    path('log/<system>/ruleset/<ruleset_name>/', log.logs_by_ruleset, name='logs_by_ruleset'),  # logs_by_ruleset
    path('integration/genian/', integration.integration_genian),
    path('integration/fortigate/', integration.integration_fortigate),
    path('integration/linux/', integration.integration_linux),
    path('integration/mssql/', integration.integration_mssql),
    path('integration/snmp/', integration.integration_snmp),
    path('integration/transmission/', integration.integration_transmission),
]

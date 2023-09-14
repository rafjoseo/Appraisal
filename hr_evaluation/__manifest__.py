# -*- coding: utf-8 -*-
{
    'name': "Performance Evaluation",

    'summary': """
        Performance Evaluation""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Dennis Lucanas",
    'website': "http://www.malayatechconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_appraisal'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_appraisal_data.xml',
        'views/hr_evaluation_views.xml',
        'views/appraisal_widget.xml',
        'views/appraisal_cycle.xml',
        'views/merit_rating.xml',
        
    ],
    'qweb': [
        'static/src/xml/appraisal_templates.xml',
        'static/src/xml/skills_templates.xml',
    ],
    'installable': True,
    'application': True,
}

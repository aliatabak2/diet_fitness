{
    "name": "Diet & Fitness (Zayıflama Uygulaması)",
    "version": "1.0.0",
    "category": "Health/Fitness",
    "summary": "Üyelik, diyet programı, öğün planı, malzeme/alternatif ve spor listeleri",
    "author": "Waresky",
    "website": "https://waresky.com",
    "license": "LGPL-3",
 
"depends": ["base","contacts","product","uom","mail","website","website_profile","portal"],

"data": [
  
    "security/diet_security.xml",      
    "security/ir.model.access.csv",
     "security/diet_portal_rules.xml",
    "views/menu.xml",
    "views/member_views.xml",
    'security/dm_rules.xml',
    'views/portal_dm_templates.xml',
   'views/res_users_views.xml',
    'security/diet_member_rules.xml',
    'views/portal_pantry_templates.xml',

    "views/program_views.xml",
    "views/nutrition_views.xml",  
    "views/exercise_views.xml",
    "views/period_views.xml",
    "views/plan_views.xml",
    
    'security/appointment_rules.xml',
    'views/appointment_views.xml',
    'views/portal_appointment_templates.xml',
    #"views/portal_avatar.xml",
    'views/portal_vip_templates.xml',
   
    "data/diet_program_data.xml",
   "views/portal_templates.xml", 
    

   
],    

'assets': {
    'web.assets_frontend': [
        'diet_fitness/static/src/scss/diet_portal.scss',
    ],
},

    "application": True,
    "installable": True,

}
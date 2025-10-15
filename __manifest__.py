{
    "name": "Diet & Fitness (Zayıflama Uygulaması)",
    "version": "1.0.0",
    "category": "Health/Fitness",
    "summary": "Üyelik, diyet programı, öğün planı, malzeme/alternatif ve spor listeleri",
    "author": "Waresky",
    "website": "https://waresky.com",
    "license": "LGPL-3",
 
"depends": ["base","contacts","product","uom","mail","website","portal"],

"data": [
  
    "security/diet_security.xml",      
    "security/ir.model.access.csv",
    "views/member_views.xml",
    "views/program_views.xml",
    "views/nutrition_views.xml",  
    "views/exercise_views.xml",
    "views/period_views.xml",
    "views/plan_views.xml",
    "views/portal_templates.xml", 

    "security/diet_portal_rules.xml",
    "data/diet_program_data.xml",
   
    "views/menu.xml",

   
],    

'assets': {
    'web.assets_frontend': [
        'diet_fitness/static/src/scss/diet_portal.scss',
    ],
},

    "application": True,
    "installable": True,

}
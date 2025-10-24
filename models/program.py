from odoo import models, fields

class DietProgram(models.Model):
    _name = "diet.program"
    _description = "Diyet Programı"

    name = fields.Char("Ad", required=True)
    pace = fields.Selection([
        ("slow", "Yavaş"),
        ("medium", "Orta"),
        ("fast", "Hızlı"),
    ], string="Tempo", default="medium", index=True)
    intensity = fields.Selection([
        ("slow", "Yavaş Kilo Verme"),
        ("medium", "Orta Hızda"),
        ("fast", "Hızlı Kilo Verme"),
    ], string="Program Tipi", required=True, index=True)

    # Önerilen kalori açığı (günlük)
    deficit_min = fields.Integer("Kalori Açığı Min", default=250)
    deficit_max = fields.Integer("Kalori Açığı Max", default=750)

    description = fields.Text("Açıklama")

    

from odoo import models, fields, api
from datetime import date


class DietWatch(models.Model):
    _name = "diet.watch"
    _description = "Akıllı Saat Verisi (Adımsayar / Kalori Takibi)"
    _order = "date desc"

    member_id = fields.Many2one("diet.member", string="Üye", required=True, ondelete="cascade")
    date = fields.Date("Tarih", default=fields.Date.context_today, required=True)

    steps = fields.Integer("Adım Sayısı", required=True, default=0)
    distance_km = fields.Float("Mesafe (km)", compute="_compute_distance", store=True)
    kcal_burned = fields.Float("Yakılan Kalori", compute="_compute_kcal_burned", store=True)

    # opsiyonel not
    note = fields.Text("Not")

    # ---- Hesaplamalar ----

    @api.depends("steps")
    def _compute_distance(self):
        """Yaklaşık adım uzunluğuna göre mesafeyi hesapla (ortalama 0.75m/adım)."""
        for rec in self:
            rec.distance_km = round((rec.steps * 0.75) / 1000, 2)

    @api.depends("steps", "member_id.activity_level")
    def _compute_kcal_burned(self):
        """Adım sayısına ve aktivite seviyesine göre yakılan kaloriyi hesapla."""
        for rec in self:
            if not rec.member_id:
                rec.kcal_burned = 0.0
                continue

            # aktivite katsayısı
            level_factor = {
                "sedentary": 0.035,
                "light": 0.04,
                "moderate": 0.045,
                "very": 0.05,
                "athlete": 0.06,
            }.get(rec.member_id.activity_level, 0.04)

            # adımlardan gelen kalori
            kcal_steps = rec.steps * level_factor

            # varsa o güne ait spor programından ekstra kcal ekle
            workout_kcal = 0
            workout_logs = rec.env["diet.workout"].search([("create_date", ">=", rec.date), ("create_date", "<", rec.date + fields.Date.delta(days=1))])
            for w in workout_logs:
                workout_kcal += w.kcal_burn or 0

            rec.kcal_burned = round(kcal_steps + workout_kcal, 2)
    @api.model("string")
    def get_watch_data_for_member_on_date(self, member_id, target_date):
        """Belirli bir üye ve tarih için saat verisini getir."""
        return self.search([("member_id", "=", member_id), ("date", "=", target_date)], limit=1)
        factor={    'member': member,
            'plan': plan,
            'total_kcal': total_kcal,
            'appt_count': appt_count,
            'recent_appts': recent_appts,
            'pantry_count': pantry_count,
        } 
    
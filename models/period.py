from odoo import models, fields, api
from datetime import timedelta

class DietPeriodPlan(models.Model):
    _name = "diet.period.plan"
    _description = "Dönemlik Plan (14 gün)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_name", store=True)
    member_id = fields.Many2one("diet.member", required=True)
    date_start = fields.Date(default=fields.Date.context_today, required=True)
    length_days = fields.Integer(default=14)
    cheat_day = fields.Integer(default=14, help="Dönemin kaçıncı günü cheat day")
    state = fields.Selection([("draft","Taslak"),("ready","Hazır"),("done","Tamamlandı")], default="draft", tracking=True)

    daily_plan_ids = fields.One2many("diet.daily.plan", "period_id", string="Günlük Planlar")
    

    @api.depends("member_id", "date_start", "length_days")
    def _compute_name(self):
        for rec in self:
            if rec.member_id and rec.date_start:
                rec.name = f"{rec.member_id.partner_id.display_name} - {rec.date_start} (+{rec.length_days}g)"
            else:
                rec.name = "Dönemlik Plan"

    # Basit BMR/TDEE + tempo (slow/medium/fast)
    def _estimate_target_kcal(self, member):
        # eksikse 2000’e sabitle
        if not (member.gender and member.height_cm and member.weight_kg and member.age):
            return 2000
        if member.gender == "male":
            bmr = 10*member.weight_kg + 6.25*member.height_cm - 5*member.age + 5
        else:
            bmr = 10*member.weight_kg + 6.25*member.height_cm - 5*member.age - 161
        level = getattr(member, "activity_level", None) or "light"
        factor_map = {"sedentary":1.2, "light":1.375, "moderate":1.55, "very":1.725, "athlete":1.9}
        factor = factor_map.get(level, 1.375)

        tdee = bmr * factor

        pace = "medium"  
        pace = "medium"
        if hasattr(member, "program_id") and member.program_id:
            pace = member.program_id.pace or "medium"
        elif hasattr(member, "pace") and member.pace:
            pace = member.pace or "medium"

        deficit = {"slow":250, "medium":500, "fast":750}.get(pace, 500)
        return max(1200, int(tdee - deficit))
      

    def action_generate_period(self):
        Daily = self.env["diet.daily.plan"].sudo()
        start = self.date_start or fields.Date.context_today(self)
        if isinstance(start, str):
            start = fields.Date.from_string(start)

        for i in range(14):
            d = start + timedelta(days=i)
        for rec in self:
            start = fields.Date.from_string(rec.date_start)
            for i in range(13):  # 13 gün
                d = start + timedelta(days=i)
                plan = Daily.search([("member_id","=",rec.member_id.id), ("date","=",d)], limit=1)
                if not plan:
                    plan = Daily.create({"member_id": rec.member_id.id, "date": d, "period_id": rec.id})
            plan.write({"target_kcal": 2200})
            plan.generate_random_meals(max_total_kcal=2200, extra_max_kcal=1000)
        rec.state = "ready"
        return True

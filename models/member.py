from odoo import models, fields, api
from math import log10
#
#samet buraya dokunma benim dediğim muhabbet daha doğru yağ oranıyla ilgili
#
class DietMember(models.Model):
    _name = "diet.member"
    _description = "Üye (Diyet/Spor)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"  # <-- EKLENDİ: seçimlerde bu alan görünsün

    # Ad Soyad'ı partnerdan çeken alan
    display_name = fields.Char(
        related="partner_id.display_name",
        string="Ad Soyad",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="Kişi", required=True, ondelete="cascade")
    program_id = fields.Many2one(
        "diet.program", string="Diyet Programı",
        ondelete="set null", index=True
    )
    gender = fields.Selection([("male", "Erkek"), ("female", "Kadın")], string="Cinsiyet", required=True)
    age = fields.Integer("Yaş", required=True)
    height_cm = fields.Float("Boy (cm)", required=True)
    weight_kg = fields.Float("Kilo (kg)", required=True, tracking=True)
    target_weight_kg = fields.Float("Hedef Kilo (kg)")

    # vücut ölçüleri
    waist_cm = fields.Float("Bel (cm)")
    hip_cm = fields.Float("Kalça (cm)")
    neck_cm = fields.Float("Boyun (cm)")
    chest_cm = fields.Float("Göğüs (cm)")

    # hesaplamalar
    bmi = fields.Float("BMI", compute="_compute_metrics", store=True)
    body_fat_pct = fields.Float("Yağ Oranı (%)", compute="_compute_metrics", store=True)

    activity_level = fields.Selection([
        ("sedentary", "Sedanter"),
        ("light", "Hafif Aktif"),
        ("moderate", "Orta Aktif"),
        ("very", "Çok Aktif"),
        ("athlete", "Atletik"),
    ], string="Aktivite", default="light", tracking=True)

    # üyenin evdeki malzemeleri 
    pantry_product_ids = fields.Many2many("product.product", string="Evdeki Malzemeler")

    log_ids = fields.One2many("diet.member.log", "member_id", string="Günlük Loglar")

    @api.depends("height_cm", "weight_kg", "gender", "waist_cm", "hip_cm", "neck_cm")
    def _compute_metrics(self):
        for rec in self:
            # BMI
            if rec.height_cm:
                rec.bmi = rec.weight_kg / ((rec.height_cm / 100.0) ** 2)
            else:
                rec.bmi = 0.0

            # basit yağ oranı formülü
            if rec.gender and rec.waist_cm and rec.neck_cm and rec.height_cm:
                try:
                    if rec.gender == "male":
                        rec.body_fat_pct = (495 / (1.0324 - 0.19077 * log10(rec.waist_cm - rec.neck_cm) + 0.15456 * log10(rec.height_cm))) - 450
                    else:
                        if rec.hip_cm:
                            rec.body_fat_pct = (495 / (1.29579 - 0.35004 * log10(rec.waist_cm + rec.hip_cm - rec.neck_cm) + 0.22100 * log10(rec.height_cm))) - 450
                        else:
                            rec.body_fat_pct = 0.0
                except Exception:
                    rec.body_fat_pct = 0.0
            else:
                rec.body_fat_pct = 0.0


class DietMemberLog(models.Model):
    _name = "diet.member.log"
    _description = "Üye Günlük Log"

    member_id = fields.Many2one("diet.member", required=True, ondelete="cascade")
    date = fields.Date("Tarih", default=fields.Date.context_today, required=True)
    weight_kg = fields.Float("Güncel Kilo (kg)")
    notes = fields.Text("Not")

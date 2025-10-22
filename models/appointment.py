# /mnt/extra-addons/diet_fitness/models/appointment.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError 
class DietAppointment(models.Model):
    _name = "diet.appointment"
    _description = "Diet Coaching/Dietitian Appointment"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Konu", required=True, tracking=True)
    type = fields.Selection(
        [("coach", "Koç"), ("dietitian", "Diyetisyen")],
        string="Tür", required=True, tracking=True, default="coach"
    )
    member_id = fields.Many2one("diet.member", string="Üye", required=True, ondelete="cascade", tracking=True)
    partner_id = fields.Many2one(related="member_id.partner_id", store=True, readonly=True)
#yalnızca constraint’e güvenmek daha iyi diye değiştirdim zaten cont ile sağlama alıyoz
    advisor_id = fields.Many2one(
    "res.users", string="Danışman (sadece admin)",
    required=True, tracking=True
)



    date_start = fields.Datetime("Başlangıç", required=True, tracking=True)
    date_end = fields.Datetime("Bitiş", required=False, tracking=True)
    note = fields.Text("Notlar")

    state = fields.Selection(
        [("request", "Talep"), ("confirm", "Onaylandı"), ("done", "Tamamlandı"), ("cancel", "İptal")],
        default="request", tracking=True, string="Durum"
    )

#basit doğrulama
    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_end <= rec.date_start:
                raise ValueError("Bitiş, başlangıçtan sonra olmalı.")
    @api.constrains("advisor_id")
    def _check_advisor_is_admin(self):
        admin_group = self.env.ref("base.group_system")
        for rec in self:
            if rec.advisor_id and admin_group not in rec.advisor_id.groups_id:
                raise ValidationError("Danışman yalnızca admin (Yönetici) olabilir.")
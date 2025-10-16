# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class DietDMThread(models.Model):
    _name = "diet.dm.thread"
    _description = "Diet Direct Message Thread"
    _order = "last_message_date desc, id desc"

    name = fields.Char(string="Ad", compute="_compute_name", store=True)
    participant_ids = fields.Many2many(
        "res.partner", "diet_dm_thread_partner_rel", "thread_id", "partner_id",
        string="Katılımcılar", required=True
    )
    message_ids = fields.One2many("diet.dm.message", "thread_id", string="Mesajlar")
    last_message_date = fields.Datetime(string="Son Mesaj", compute="_compute_counters", store=True)
    message_count = fields.Integer(string="Mesaj Sayısı", compute="_compute_counters", store=True)

    @api.depends("participant_ids", "message_ids.body", "message_ids.create_date")
    def _compute_counters(self):
        for t in self:
            t.message_count = len(t.message_ids)
            t.last_message_date = t.message_ids[:1].create_date if t.message_ids else False

    @api.depends("participant_ids")
    def _compute_name(self):
        user_partner = self.env.user.partner_id
        for t in self:
            others = t.participant_ids - user_partner
            if len(others) == 1:
                t.name = _("Siz ve %s") % (others.name)
            else:
                t.name = ", ".join(others.mapped("name")) or _("Sohbet")

    def check_participation_or_raise(self):
        me = self.env.user.partner_id
        for t in self:
            if me not in t.participant_ids:
                raise AccessError(_("Bu sohbet size ait değil."))

    @api.model
    def get_or_create_pair_thread(self, partner_a, partner_b):
        # Aynı iki kişi için tek thread
        all_threads = self.search([
            ("participant_ids", "in", [partner_a.id]),
            ("participant_ids", "in", [partner_b.id]),
        ], limit=1)
        if all_threads:
            return all_threads
        return self.create({"participant_ids": [(6, 0, [partner_a.id, partner_b.id])]})

class DietDMMessage(models.Model):
    _name = "diet.dm.message"
    _description = "Diet Direct Message"
    _order = "id asc"

    thread_id = fields.Many2one("diet.dm.thread", required=True, ondelete="cascade")
    author_id = fields.Many2one("res.partner", required=True, default=lambda self: self.env.user.partner_id)
    body = fields.Text("Mesaj", required=True)
    create_date = fields.Datetime(readonly=True)

    def check_participation_or_raise(self):
        me = self.env.user.partner_id
        for m in self:
            if me not in m.thread_id.participant_ids:
                raise AccessError(_("Bu sohbet size ait değil."))

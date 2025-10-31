# -*- coding: utf-8 -*-
import os
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL    = "gpt-4o-mini"  # dilediğinizi koyun

class DietAIThread(models.Model):
    _name = "diet.ai.thread"
    _description = "AI Chat Thread"
    _order = "id desc"

    name = fields.Char(default="Sohbet", required=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    message_ids = fields.One2many("diet.ai.message", "thread_id", string="Mesajlar")
    last_answer = fields.Text("Son Cevap", readonly=True)

    def _check_owner(self):
        user_partner = self.env.user.partner_id
        for rec in self:
            if rec.partner_id != user_partner and not self.env.user.has_group("base.group_system"):
                raise AccessError(_("Bu sohbet size ait değil."))

    def _get_api_key(self):
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param("openai.api_key") or os.getenv("OPENAI_API_KEY")

    def action_ask(self, prompt):
        self._check_owner()
        api_key = self._get_api_key()
        if not api_key:
            raise UserError(_("OpenAI API anahtarı ayarlanmamış (openai.api_key)."))

        # Geçmişi topla (son 10 mesaj)
        history = []
        msgs = self.message_ids.sorted("id")[-10:]
        for m in msgs:
            role = "assistant" if m.role == "assistant" else "user"
            history.append({"role": role, "content": m.content or ""})
        # son kullanıcı mesajı (prompt)
        history.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": history,
            "temperature": 0.3,
        }

        resp = requests.post(OPENAI_ENDPOINT, json=payload, headers=headers, timeout=60)
        if resp.status_code >= 400:
            raise UserError(_("OpenAI hata: %s") % resp.text)

        data = resp.json()
        answer = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        # kayıtlar
        self.env["diet.ai.message"].sudo().create({
            "thread_id": self.id,
            "role": "user",
            "content": prompt,
        })
        self.env["diet.ai.message"].sudo().create({
            "thread_id": self.id,
            "role": "assistant",
            "content": answer,
        })
        self.write({"last_answer": answer})
        return answer


class DietAIMessage(models.Model):
    _name = "diet.ai.message"
    _description = "AI Chat Message"
    _order = "id asc"

    thread_id = fields.Many2one("diet.ai.thread", required=True, ondelete="cascade", index=True)
    role = fields.Selection([("user", "Kullanıcı"), ("assistant", "Asistan")], required=True)
    content = fields.Text(required=True)
    partner_id = fields.Many2one(related="thread_id.partner_id", store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        # sahiplik kontrolü
        for rec in recs:
            if rec.partner_id != self.env.user.partner_id and not self.env.user.has_group("base.group_system"):
                raise AccessError(_("Bu mesaja erişim yetkiniz yok."))
        return recs

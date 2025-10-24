# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

def _member_partner():
    return request.env.user.partner_id

class DietAIPortal(http.Controller):

    @http.route(['/my/account/ai'], type='http', auth='user', website=True)
    def portal_ai_home(self, **kw):
        partner = _member_partner()
        Thread = request.env["diet.ai.thread"].sudo()
        thread = Thread.search([("partner_id", "=", partner.id)], limit=1)
        if not thread:
            thread = Thread.create({"partner_id": partner.id, "name": "Sohbetim"})
        # mesajlar
        msgs = request.env["diet.ai.message"].sudo().search([("thread_id", "=", thread.id)])
        return request.render("diet_fitness.portal_ai_chat", {
            "thread": thread,
            "messages": msgs,
        })

    @http.route(['/my/account/ai/ask'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_ai_ask(self, **post):
        prompt = (post.get("prompt") or "").strip()
        if not prompt:
            return request.redirect("/my/account/ai")
        partner = _member_partner()
        Thread = request.env["diet.ai.thread"].sudo()
        thread = Thread.search([("partner_id", "=", partner.id)], limit=1)
        if not thread:
            thread = Thread.create({"partner_id": partner.id, "name": "Sohbetim"})
        # çağrı
        thread.action_ask(prompt)
        return request.redirect("/my/account/ai")

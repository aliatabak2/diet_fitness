# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

def _my_member():
    return request.env['diet.member'].sudo().search([('partner_id','=',request.env.user.partner_id.id)], limit=1)

class DietDMPortal(http.Controller):

    # Üye listesi
    @http.route(['/my/diet/members'], type='http', auth='user', website=True)
    def member_list(self, **kw):
        me = request.env.user.partner_id
        members = request.env['diet.member'].sudo().search([])
        # Kendini filtrele
        members = members.filtered(lambda m: m.partner_id.id != me.id)
        return request.render('diet_fitness.portal_member_list', {'members': members})

    # DM gelen kutusu (sohbet listesi)
    @http.route(['/my/diet/messages'], type='http', auth='user', website=True)
    def dm_inbox(self, **kw):
        me = request.env.user.partner_id
        threads = request.env['diet.dm.thread'].sudo().search([
            ('participant_ids','in',[me.id])
        ], order="last_message_date desc, id desc")
        return request.render('diet_fitness.portal_dm_inbox', {'threads': threads})

    # Belirli üyeye mesaj başlat (veya var olanı aç)
    @http.route(['/my/diet/messages/start/<int:partner_id>'], type='http', auth='user', website=True)
    def dm_start(self, partner_id, **kw):
        me = request.env.user.partner_id
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists() or partner.id == me.id:
            return request.redirect('/my/diet/members')
        thread = request.env['diet.dm.thread'].sudo().get_or_create_pair_thread(me, partner)
        return request.redirect(f"/my/diet/messages/{thread.id}")

    # Sohbet detayı
    @http.route(['/my/diet/messages/<int:thread_id>'], type='http', auth='user', website=True)
    def dm_thread(self, thread_id, **kw):
        thread = request.env['diet.dm.thread'].sudo().browse(thread_id)
        try:
            thread.check_participation_or_raise()
        except AccessError:
            return request.redirect('/my/diet/messages')
        return request.render('diet_fitness.portal_dm_thread', {'thread': thread})

    # Mesaj gönder (POST + CSRF)
    @http.route(['/my/diet/messages/<int:thread_id>/send'], type='http', auth='user',
                methods=['POST'], csrf=True, website=True)
    def dm_send(self, thread_id, **post):
        body = (post.get('body') or '').strip()
        thread = request.env['diet.dm.thread'].sudo().browse(thread_id)
        try:
            thread.check_participation_or_raise()
        except AccessError:
            return request.redirect('/my/diet/messages')
        if body:
            request.env['diet.dm.message'].sudo().create({
                'thread_id': thread.id,
                'author_id': request.env.user.partner_id.id,
                'body': body,
            })
        return request.redirect(f"/my/diet/messages/{thread.id}")

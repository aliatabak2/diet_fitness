# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class VipPortal(CustomerPortal):

    @http.route(['/my'], type='http', auth='user', website=True, sitemap=False)
    def home(self, **kw):
        """VIP ise /my-vip'e yönlendir, değilse standart portalı aç."""
        user = request.env.user.sudo()
        # Boolean alan ile kontrol (istersen group bazlı hale getirebilirsin)
        if getattr(user, 'is_portal_vip', False):
            return request.redirect('/my-vip')
        return super(VipPortal, self).home(**kw)

    @http.route(['/my-vip'], type='http', auth='user', website=True, sitemap=False)
    def my_vip_home(self, **kw):
        """VIP ana ekranı: bugünkü plan, randevu sayısı, son randevular, kiler (pantry) sayısı."""
        user = request.env.user.sudo()
        partner = user.partner_id

        # Üyeyi bul
        Member = request.env['diet.member'].sudo()
        member = Member.search([('partner_id', '=', partner.id)], limit=1)

        # Bugünkü planı bul (gerekirse oluştur)
        plan = False
        total_kcal = 0
        if member:
            today = fields.Date.context_today(request.env.user)
            Plan = request.env['diet.daily.plan'].sudo()
            plan = Plan.search([('member_id', '=', member.id), ('date', '=', today)], limit=1)
            if not plan:
                # Herhangi bir program ata (ilk bulunan); senin standart /my akışınla aynı mantık
                prog = request.env['diet.program'].sudo().search([], limit=1)
                vals = {'member_id': member.id, 'date': today}
                if prog:
                    vals['program_id'] = prog.id
                plan = Plan.create(vals)
                # Oto-öğün üret
                if hasattr(plan, 'action_generate_meals'):
                    plan.action_generate_meals()
            # Toplam kcal
            if plan:
                try:
                    total_kcal = sum(plan.meal_line_ids.mapped('kcal')) or 0
                except Exception:
                    total_kcal = 0

        # Randevular
        Appt = request.env['diet.appointment'].sudo()
        appt_domain = [('partner_id', '=', partner.id)]
        appt_count = Appt.search_count(appt_domain)
        recent_appts = Appt.search(appt_domain, order="date_start desc", limit=5)

        # Pantry (kiler) sayısı
        pantry_count = len(member.pantry_product_ids) if member else 0

        values = {
            'user': user,
            'is_vip': True,
            'member': member,
            'plan': plan,
            'total_kcal': total_kcal,
            'appt_count': appt_count,
            'recent_appts': recent_appts,
            'pantry_count': pantry_count,
        }
        return request.render('diet_fitness.portal_my_vip', values)

# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class VipPortal(CustomerPortal):
    @http.route(['/my'], type='http', auth='user', website=True, sitemap=False)
    def home(self, **kw):
        """VIP ise /my-vip'e yönlendir, değilse standart portalı aç."""
        user = request.env.user.sudo()
        if getattr(user, 'is_portal_vip', False):
            return request.redirect('/my-vip')
        return super(VipPortal, self).home(**kw)

    @http.route(['/my-vip'], type='http', auth='user', website=True, sitemap=False)
    def my_vip_home(self, **kw):
        """VIP ana ekranı (şimdilik normal /my ile aynı görünüm)."""
        #vip ayrıcalıkları buraya
        values = {
            'user': request.env.user,
            'is_vip': True,
        }
        return request.render('diet_fitness.portal_my_vip', values)

# /mnt/extra-addons/diet_fitness/controllers/diet_portal_appointment.py
from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta

def _member_for_current_user():
    partner = request.env.user.partner_id
    return request.env['diet.member'].sudo().search([('partner_id','=',partner.id)], limit=1)

class DietPortalAppointment(http.Controller):

    @http.route(['/my/diet/appointments'], type='http', auth='user', website=True)
    def portal_appointments(self, **kw):
        member = _member_for_current_user()
        domain = [('partner_id','=', request.env.user.partner_id.id)]
        appts = request.env['diet.appointment'].sudo().search(domain, order='date_start desc', limit=50)
        return request.render('diet_fitness.portal_appointment_list', {
            'member': member,
            'appts': appts,
        })

    @http.route(['/my/diet/appointment/new'], type='http', auth='user', website=True)
    def portal_appointment_new(self, **kw):
        # danışman havuzu: sadece admin kullanıcılar
        advisors = request.env['res.users'].sudo().search([('groups_id','in',[request.env.ref('base.group_system').id])])
        member = _member_for_current_user()
        return request.render('diet_fitness.portal_appointment_new', {
            'member': member,
            'advisors': advisors,
            'default_date': fields.Datetime.now(),
        })
  
    @http.route(['/my/diet/appointment/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_appointment_create(self, **post):
        member = _member_for_current_user()
        if not member:
            return request.redirect('/my/diet')

        vals = {
            'name': post.get('name') or 'Görüşme',
            'type': post.get('type') or 'coach',
            'member_id': member.id,
            'advisor_id': int(post.get('advisor_id')) if post.get('advisor_id') else request.env.user.id,
            'date_start': post.get('date_start'),
            'date_end': post.get('date_end'),
            'note': post.get('note'),   
            'state': 'request',
        }
        request.env['diet.appointment'].sudo().create(vals)
        return request.redirect('/my/diet/appointments')
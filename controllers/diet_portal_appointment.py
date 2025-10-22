# /mnt/extra-addons/diet_fitness/controllers/diet_portal_appointment.py
from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta



#odoo malı dd mm yy h ss olarak kabul ettiği için default time format değiştim
def _norm_dt(val):
    """HTML datetime-local => 'YYYY-MM-DD HH:MM:SS' string"""
    if not val:
        return False
    s = val.strip().replace('T', ' ')
    if len(s) == 16:  
        s += ':00'
    return s

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
# danışman havuzu: sadece atanmis kişileri gözter
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
        start_s = _norm_dt(post.get('date_start'))
        end_s   = _norm_dt(post.get('date_end'))

        vals = {
            'name': post.get('name') or 'Görüşme',
            'type': post.get('type') or 'coach',
            'member_id': member.id,
            'advisor_id': int(post.get('advisor_id')) if post.get('advisor_id') else request.env.user.id,
            'date_start': start_s,
            'date_end': end_s,
            'note': post.get('note'),   
            'state': 'request',
        }
        request.env['diet.appointment'].sudo().create(vals)
        return request.redirect('/my/diet/appointments')
    

#yollanan randevu talebi kabul red

    @http.route(['/my/diet/appointment/<int:appt_id>/confirm'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def appt_confirm(self, appt_id, **post):
        appt = request.env['diet.appointment'].sudo().browse(appt_id)
        if not appt:
            return request.redirect('/my/diet/appointments')
#erişim kontrolü: sadece atanan danışman veya admin
        admin_group = request.env.ref("base.group_system")
        user = request.env.user
        if not (user.id == appt.advisor_id.id or admin_group in user.groups_id):
            return request.redirect('/my/diet/appointments')
        appt.action_confirm()
        return request.redirect('/my/diet/appointments')

    @http.route(['/my/diet/appointment/<int:appt_id>/cancel'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def appt_cancel(self, appt_id, **post):
        appt = request.env['diet.appointment'].sudo().browse(appt_id)
        if not appt:
            return request.redirect('/my/diet/appointments')
        admin_group = request.env.ref("base.group_system")
        user = request.env.user
        if not (user.id == appt.advisor_id.id or admin_group in user.groups_id):
            return request.redirect('/my/diet/appointments')
        appt.action_cancel()
        return request.redirect('/my/diet/appointments')

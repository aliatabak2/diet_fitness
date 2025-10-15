from odoo import http, fields
from odoo.http import request
from datetime import date
from datetime import date, timedelta


class DietPortal(http.Controller):

    @http.route(['/my/diet', '/my/diet/<string:date_str>'], type='http', auth='user', website=True)
    def portal_diet(self, date_str=None, **kw):
        partner = request.env.user.partner_id
        member = request.env['diet.member'].sudo().search([('partner_id','=',partner.id)], limit=1)
        if not member:
            return request.render('diet_fitness.portal_no_member', {})

        the_date = date.fromisoformat(date_str) if date_str else fields.Date.context_today(request.env.user)
        Plan = request.env['diet.daily.plan'].sudo()
        plan = Plan.search([('member_id','=',member.id), ('date','=',the_date)], limit=1)
        if not plan:
            prog = request.env['diet.program'].sudo().search([], limit=1)
            if prog:
                plan = Plan.create({'member_id': member.id, 'program_id': prog.id, 'date': the_date})
                plan.action_generate_meals()

        values = {'member': member, 'plan': plan}
        return request.render('diet_fitness.portal_diet_plan', values)

    @http.route('/my/diet/line/<int:line_id>/toggle', type='json', auth='user', methods=['POST'])
    def toggle_meal_done(self, line_id):
        line = request.env['diet.daily.meal.line'].sudo().browse(line_id)
        if not line or line.plan_id.member_id.partner_id.id != request.env.user.partner_id.id:
            return {'ok': False}
        line.is_done = not line.is_done
        return {'ok': True, 'is_done': line.is_done}

    ""
    @http.route(
        ['/my/diet/plan/<int:plan_id>/regen'],
        type='http', auth='user', methods=['POST'], website=True ,  csrf=False
    )
    def my_diet_plan_regen(self, plan_id, **post):
        # Üye doğrulama
        member = request.env['diet.member'].sudo().search(
            [('partner_id', '=', request.env.user.partner_id.id)], limit=1
        )
        plan = request.env['diet.daily.plan'].sudo().browse(plan_id)

        if not plan or not member or plan.member_id.id != member.id:
            return request.redirect('/my/diet')

        # Günlük menüyü tekrar üret
        plan.generate_random_meals(max_total_kcal=2200, extra_max_kcal=1000)

        # Plan detayına dön
        return request.redirect(f'/my/diet/plan/{plan_id}')
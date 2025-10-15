# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date, timedelta
from collections import defaultdict

def _member_for_current_user():
    partner = request.env.user.partner_id
    return request.env['diet.member'].sudo().search([('partner_id', '=', partner.id)], limit=1)

def _ensure_own_record(record, member):
    # Basit sahiplik kontrolü
    if not record or not member or record.member_id.id != member.id:
        return False
    return True

class DietPortal(http.Controller):

    @http.route(['/my/diet/workouts'], type='http', auth='user', website=True)
    def my_diet_workouts(self, **kw):
        member = _member_for_current_user()
        Daily = request.env['diet.daily.plan'].sudo()
        # Son 7 gün + gelecek 14 gün (ihtiyaca göre ayarla)
        today = date.today()
        start = today - timedelta(days=7)
        end   = today + timedelta(days=14)
        dom = [('member_id', '=', member.id), ('date', '>=', start), ('date', '<=', end)]
        plans = Daily.search(dom, order='date asc')
        return request.render('diet_fitness.portal_workout_list_v2', {
            'member': member,
            'plans': plans,
            'today': today,
        })

    # SPOR DETAY (plan'a bağlı workout göster)
    @http.route(['/my/diet/workout/<int:plan_id>'], type='http', auth='user', website=True)
    def my_diet_workout_detail(self, plan_id, **kw):
        member = _member_for_current_user()
        plan = request.env['diet.daily.plan'].sudo().browse(plan_id)
        if not _ensure_own_record(plan, member):
            return request.redirect('/my/diet/workouts')
        workout = plan.workout_id  # Many2one(diet.workout)
        return request.render('diet_fitness.portal_workout_detail', {
            'member': member,
            'plan': plan,
            'workout': workout,
        })

    # SPORU TAMAMLANDI İŞARETLE
    @http.route(['/my/diet/workout/<int:plan_id>/done'], type='http', auth='user', methods=['POST'], csrf=False, website=True)
    def my_diet_workout_done(self, plan_id, **post):
        member = _member_for_current_user()
        plan = request.env['diet.daily.plan'].sudo().browse(plan_id)
        if not _ensure_own_record(plan, member):
            return request.redirect('/my/diet/workouts')
        plan.sudo().write({'workout_done': True})
        return request.redirect(f'/my/diet/workout/{plan_id}')
    
    
    
    
    @http.route(['/my/diet'], type='http', auth='user', website=True)
    def my_diet_dashboard(self, **kw):
        member = _member_for_current_user()
        Daily = request.env['diet.daily.plan'].sudo()
        Period = request.env['diet.period.plan'].sudo()

        plans = Daily.search([('member_id', '=', member.id)], limit=14, order='date desc') if member else Daily.browse()
        periods = Period.search([('member_id', '=', member.id)], limit=5, order='id desc') if member else Period.browse()

        # güvenli toplamlar
        plan_totals = {p.id: sum(p.meal_line_ids.mapped('kcal')) for p in plans}

        return request.render('diet_fitness.portal_my_diet', {
            'member': member,
            'plans': plans,
            'periods': periods,
            'plan_totals': plan_totals,
        })
    # GÜNLÜK PLAN DETAY
    @http.route(['/my/diet/plan/<int:plan_id>'], type='http', auth='user', website=True)
    def my_diet_plan(self, plan_id, **kw):
        member = _member_for_current_user()
        plan = request.env['diet.daily.plan'].sudo().browse(plan_id)
        if not _ensure_own_record(plan, member):
            return request.redirect('/my/diet')

        return request.render('diet_fitness.portal_plan_detail', {
            'member': member,
            'plan': plan,
            'total_kcal': sum(plan.meal_line_ids.mapped('kcal')),
        })

    # GÜNLÜK PLAN YENİDEN OLUŞTUR (POST)
    @http.route(['/my/diet/plan/<int:plan_id>/regen'], type='http', auth='user', methods=['POST'], csrf=False, website=True)
    def my_diet_plan_regen(self, plan_id, **post):
        member = _member_for_current_user()
        plan = request.env['diet.daily.plan'].sudo().browse(plan_id)
        if not _ensure_own_record(plan, member):
            return request.redirect('/my/diet')

        plan.generate_random_meals(max_total_kcal=2200, extra_max_kcal=1000)
        return request.redirect(f'/my/diet/plan/{plan_id}')

    # DÖNEM LİSTESİ
    @http.route(['/my/diet/periods'], type='http', auth='user', website=True)
    def my_diet_periods(self, **kw):
        member = _member_for_current_user()
        Period = request.env['diet.period.plan'].sudo()
        periods = Period.search([('member_id', '=', member.id)], order='id desc') if member else Period.browse()
        return request.render('diet_fitness.portal_period_list', {
            'member': member,
            'periods': periods,
        })

    # DÖNEM DETAY + ÜRET
    @http.route(['/my/diet/period/<int:period_id>'], type='http', auth='user', website=True)
    def my_diet_period_detail(self, period_id, **kw):
        member = _member_for_current_user()
        period = request.env['diet.period.plan'].sudo().browse(period_id)
        if not period or period.member_id.id != (member.id if member else 0):
            return request.redirect('/my/diet/periods')
        days = period.daily_plan_ids.sorted(key=lambda p: p.date or date.min)
        return request.render('diet_fitness.portal_period_detail', {
            'member': member,
            'period': period,
            'days': days,
        })

    # DÖNEM: 13 GÜN ÜRET (POST)
    @http.route(['/my/diet/period/<int:period_id>/generate13'], type='http', auth='user', methods=['POST'], csrf=False, website=True)
    def my_diet_period_generate(self, period_id, **post):
        member = _member_for_current_user()
        period = request.env['diet.period.plan'].sudo().browse(period_id)
        if not period or period.member_id.id != (member.id if member else 0):
            return request.redirect('/my/diet/periods')

        # 13 gün üret (günlük limitler: 2200 / 1000)
        Daily = request.env['diet.daily.plan'].sudo()
        start = period.date_start or date.today()
        for i in range(13):
            d = start + timedelta(days=i)
            plan = Daily.search([('member_id', '=', member.id), ('date', '=', d)], limit=1)
            if not plan:
                plan = Daily.create({'member_id': member.id, 'date': d, 'period_id': period.id})
            plan.write({'target_kcal': 2200})
            plan.generate_random_meals(max_total_kcal=2200, extra_max_kcal=1000)

        period.state = 'ready'
        return request.redirect(f'/my/diet/period/{period_id}')

    # TARİF LİSTESİ
    @http.route(['/my/diet/recipes'], type='http', auth='user', website=True)
    def my_diet_recipes(self, **kw):
        course = kw.get('course')
        Recipe = request.env['diet.recipe'].sudo()
        dom = []
        if course:
            dom.append(('course', '=', course))
        recipes = Recipe.search(dom, order='name asc', limit=100)
        return request.render('diet_fitness.portal_recipe_list', {
            'recipes': recipes,
            'course': course or '',
        })

    # ALIŞVERİŞ LİSTESİ (DÖNEMDEN)
    @http.route(['/my/diet/shopping-list/<int:period_id>'], type='http', auth='user', website=True)
    def my_diet_shopping(self, period_id, **kw):
        member = _member_for_current_user()
        period = request.env['diet.period.plan'].sudo().browse(period_id)
        if not _ensure_own_record(period, member):
            return request.redirect('/my/diet')

        # Period içindeki tüm günlük planların tariflerinden malzeme konsolidasyonu
        lines = request.env['diet.daily.meal.line'].sudo().search([
            ('plan_id.period_id', '=', period.id)
        ])
        recipe_ids = lines.mapped('recipe_id').ids
        ingr = request.env['diet.recipe.line'].sudo().search([
            ('recipe_id', 'in', recipe_ids)
        ])

        bucket = defaultdict(lambda: {'uom': None, 'qty': 0.0})
        for l in ingr:
            key = l.product_id.display_name
            bucket[key]['qty'] += l.qty or 0.0
            bucket[key]['uom'] = l.uom_id.name if l.uom_id else ''

        items = [{'name': k, 'qty': v['qty'], 'uom': v['uom']} for k, v in bucket.items()]
        items.sort(key=lambda x: x['name'])

        return request.render('diet_fitness.portal_shopping_list', {
            'period': period,
            'items': items,
        })




class DietPortalDebug(http.Controller):
    @http.route(['/my/diet/ping'], type='http', auth='public', website=True)
    def diet_ping(self, **kw):
        return request.make_response("pong")
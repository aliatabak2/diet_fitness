from odoo import http, fields
from odoo.http import request

def _member_for_current_user():
    partner = request.env.user.partner_id
    return request.env['diet.member'].sudo().search([('partner_id', '=', partner.id)], limit=1)

def _ensure_own_member(member):
    return bool(member and member.partner_id.id == request.env.user.partner_id.id)

def _parse_int_ids(seq):
    ids_ = []
    for x in (seq or []):
        if x and str(x).isdigit():
            ids_.append(int(x))
    return ids_
class DietPortalPantry(http.Controller):

    @http.route(['/my/diet/pantry'], type='http', auth='user', website=True)
    def pantry_page(self, **kw):
        member = _member_for_current_user()
        if not member:
            return request.redirect('/my')

        #ürün havuzu
        Product = request.env['product.product'].sudo()
        products = Product.search([('sale_ok', '=', True)], limit=500, order='name asc')

        return request.render('diet_fitness.portal_pantry', {
            'member': member,
            'products': products,
            'selected_ids': set(member.pantry_product_ids.ids),
        })

    @http.route(['/my/diet/pantry/save'], type='http', auth='user', website=True, methods=['POST'])
    def pantry_save(self, **post):
        member = _member_for_current_user()
        if not member:
            return request.redirect('/my')

        #çoklu select et name="product_ids"
        raw_ids = request.httprequest.form.getlist('product_ids')
        try:
            ids = [int(x) for x in raw_ids]
        except Exception:
            ids = []

        if not raw_ids:
            single = request.httprequest.form.get('product_ids')
            if single:
                raw_ids = [single]

        prod_ids = _parse_int_ids(raw_ids)

        member.sudo().write({'pantry_product_ids': [(6, 0, prod_ids)]})
#kendi kaydına yaz
       
        return request.redirect('/my/diet/pantry')

from odoo import http, fields
from odoo.http import request

def _member_for_current_user():
    partner = request.env.user.partner_id
    return request.env['diet.member'].sudo().search([('partner_id', '=', partner.id)], limit=1)

class DietPortalPantry(http.Controller):

    @http.route(['/my/diet/pantry'], type='http', auth='user', website=True)
    def pantry_page(self, **kw):
        member = _member_for_current_user()
        if not member:
            return request.redirect('/my')

        # Seçtirilecek ürün havuzu (gerekiyorsa domaini daralt)
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

        # Çoklu select name="product_ids"
        raw_ids = post.getlist('product_ids')
        try:
            ids = [int(x) for x in raw_ids]
        except Exception:
            ids = []

        # Kendi kaydına yaz (ACL+rule zaten kısıtlıyor)
        member.write({'pantry_product_ids': [(6, 0, ids)]})
        return request.redirect('/my/diet/pantry')

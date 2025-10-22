
import base64
from odoo import http
from odoo.http import request

class PortalAvatar(http.Controller):

    @http.route(['/my/account/avatar'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def set_avatar(self, **post):
        # /my/account sayfasındaki formdan gelen dosya
        file = request.httprequest.files.get('avatar')
        if file and file.filename:
            data = file.read()
            b64 = base64.b64encode(data)
            # Kendi partner kaydına yaz
            request.env.user.partner_id.sudo().write({'image_1920': b64})
        return request.redirect('/my/account')

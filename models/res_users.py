from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_portal_vip = fields.Boolean(
        string="VIP Kullanıcı",
        compute="_compute_is_portal_vip",
        inverse="_inverse_is_portal_vip",
        store=False
    )

    def _compute_is_portal_vip(self):
        vip_group = self.env.ref('diet_fitness.group_portal_vip', raise_if_not_found=False)
        for user in self:
            user.is_portal_vip = bool(vip_group) and vip_group in user.groups_id

    def _inverse_is_portal_vip(self):
        vip_group = self.env.ref('diet_fitness.group_portal_vip', raise_if_not_found=False)
        if not vip_group:
            return
        for user in self:
            if user.is_portal_vip:
                user.groups_id |= vip_group
            else:
                user.groups_id -= vip_group

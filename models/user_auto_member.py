from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        self._create_member_for_portal(users)
        return users

    def write(self, vals):
        res = super().write(vals)
        self._create_member_for_portal(self)
        return res

    def _create_member_for_portal(self, users):
        """Portal grubundaki her kullanıcı için -yoksa- diet.member oluştur.
        Hata olursa savepoint ile yut; signup/grant portal kırılmasın."""
        Member = self.env["diet.member"].sudo()
        # portal grubu güvenli elde et
        try:
            portal_group = self.env.ref("base.group_portal")  # raise_if_not_found kw kullanma (bazı sürümlerde yok)
        except Exception:
            portal_group = self.env["res.groups"].browse()

        for u in users:
            try:
                if not u.partner_id:
                    continue
                # Kullanıcı gerçekten portal mı? (write sırasında grup atanır)
                if not u.has_group("base.group_portal"):
                    continue
                # Zaten varsa ikileme
                if Member.search_count([("partner_id", "=", u.partner_id.id)]):
                    continue
                # Her ihtimale karşı transaction'ı bozmasın diye savepoint
                with self.env.cr.savepoint():
                    Member.create({"partner_id": u.partner_id.id})
            except Exception as e:
                _logger.exception("Auto-create diet.member failed for user %s: %s", u.id, e)
                # hatayı yut; kullanıcı oluşturma devam etsin
                continue

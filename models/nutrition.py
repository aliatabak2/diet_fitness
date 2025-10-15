from odoo import models, fields, api

class DietRecipe(models.Model):
    _name = "diet.recipe"
    _description = "Yemek (Tarif)"
    
    is_cheat = fields.Boolean("Cheat Day Uygun", default=False)

    course = fields.Selection([
    ("salad", "Salata"),
    ("soup", "Çorba"),
    ("meal", "Yemek"),
    ("side", "Yan Yiyecek"),
], string="Tür", default="meal", index=True)


    name = fields.Char("Yemek Adı", required=True)
    description = fields.Text("Açıklama")
    line_ids = fields.One2many("diet.recipe.line", "recipe_id", string="Malzemeler")

    is_simple = fields.Boolean("Basit Öğün?", default=False,
                               help="Evde malzeme azsa önerilecek basit tarif.")

    # Elle giriş seçeneği + manuel alanlar
    use_manual_nutrition = fields.Boolean("Besin değerlerini elle gir", default=False)
    kcal_manual    = fields.Float("Kalori (elle)")
    protein_manual = fields.Float("Protein (g) (elle)")
    carbs_manual   = fields.Float("Karbonhidrat (g) (elle)")
    fat_manual     = fields.Float("Yağ (g) (elle)")

    # Gösterilen besin alanları (compute + inverse = hem otomatik hem manuel)
    kcal      = fields.Float("Kalori (kcal)", compute="_compute_nutrition",
                             inverse="_inverse_nutrition", store=True)
    protein_g = fields.Float("Protein (g)", compute="_compute_nutrition",
                             inverse="_inverse_nutrition", store=True)
    carbs_g   = fields.Float("Karbonhidrat (g)", compute="_compute_nutrition",
                             inverse="_inverse_nutrition", store=True)
    fat_g     = fields.Float("Yağ (g)", compute="_compute_nutrition",
                             inverse="_inverse_nutrition", store=True)

    @api.depends(
        "use_manual_nutrition",
        "kcal_manual", "protein_manual", "carbs_manual", "fat_manual",
        "line_ids", "line_ids.product_id", "line_ids.qty", "line_ids.uom_id"
    )
    def _compute_nutrition(self):
        for rec in self:
            if rec.use_manual_nutrition:
                rec.kcal       = rec.kcal_manual or 0.0
                rec.protein_g  = rec.protein_manual or 0.0
                rec.carbs_g    = rec.carbs_manual or 0.0
                rec.fat_g      = rec.fat_manual or 0.0
                continue

            kcal = protein = carbs = fat = 0.0
            for line in rec.line_ids:
                qty = line.qty or 0.0
                prod = line.product_id
                kcal    += float(getattr(prod, "kcal_per_uom",    0.0) or 0.0) * qty
                protein += float(getattr(prod, "protein_per_uom", 0.0) or 0.0) * qty
                carbs   += float(getattr(prod, "carbs_per_uom",   0.0) or 0.0) * qty
                fat     += float(getattr(prod, "fat_per_uom",     0.0) or 0.0) * qty
            rec.kcal = kcal
            rec.protein_g = protein
            rec.carbs_g = carbs
            rec.fat_g = fat

    def _inverse_nutrition(self):
        """Kullanıcı besin alanlarını elle değiştirirse manuel alanlara yansıt."""
        for rec in self:
            if rec.use_manual_nutrition:
                rec.kcal_manual    = rec.kcal or 0.0
                rec.protein_manual = rec.protein_g or 0.0
                rec.carbs_manual   = rec.carbs_g or 0.0
                rec.fat_manual     = rec.fat_g or 0.0


class DietRecipeLine(models.Model):
    _name = "diet.recipe.line"
    _description = "Yemek Malzemesi"

    recipe_id = fields.Many2one("diet.recipe", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Malzeme", required=True)
    qty = fields.Float("Miktar", default=1.0, required=True)
    uom_id = fields.Many2one("uom.uom", string="Birim", required=True)

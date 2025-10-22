import random
from odoo import models, fields, api

from math import floor
from random import Random
from datetime import date, timedelta

class DietDailyPlan(models.Model):
    _name = "diet.daily.plan"
    _description = "Günlük Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    

    name = fields.Char("Ad", compute="_compute_name", store=True)
    member_id = fields.Many2one("diet.member", required=True, ondelete="cascade")
    program_id = fields.Many2one(
        "diet.program", string="Diyet Programı",
        related="member_id.program_id", store=True, readonly=True
    )
    date = fields.Date("Tarih", default=fields.Date.context_today, required=True)
    period_id = fields.Many2one("diet.period.plan", string="Dönem", ondelete="cascade")
    target_kcal = fields.Integer("Hedef Kalori (günlük)", compute="_compute_target", store=True)
    meal_line_ids = fields.One2many("diet.daily.meal.line", "plan_id", string="Öğünler")
    workout_id = fields.Many2one("diet.workout", string="Spor Listesi")
    
    
    workout_done = fields.Boolean("Spor yapıldı", default=False, tracking=True)


    state = fields.Selection([
        ("draft", "Taslak"),
        ("ready", "Hazır"),
        ("done", "Tamamlandı"),
    ], default="draft", string="Durum", tracking=True)

    def _pantry_ok(self, recipe, have_ids):
        """Tarifin tüm malzemeleri evde var mı?"""
        if not recipe:
            return False
        for l in recipe.line_ids:
            if l.product_id.id not in have_ids:
                return False
        return True
    
    def _recent_recipe_ids(self, member, days=3):
        """Son X günde kullanılan tarifleri dışlamak için ID seti."""
        if not member:
            return set()
        DailyLine = self.env["diet.daily.meal.line"].sudo()
        today = fields.Date.context_today(self)
        start = fields.Date.to_date(today) - timedelta(days=days)
        lines = DailyLine.search([
            ('plan_id.member_id', '=', member.id),
            ('plan_id.date', '>=', start),
        ])
        return set(lines.mapped('recipe_id').ids)

    def _candidate_pool(self, base_domain, kcal_max, member, used_ids, require_pantry=True, limit=120):
        """Domain + kcal + tekrar + kiler koşulları ile havuz oluştur."""
        Recipe = self.env["diet.recipe"].sudo()

        dom = list(base_domain)
        if kcal_max is not None:
            dom += [('kcal', '<=', max(0, int(kcal_max)))]

        # Önce geniş bir havuz çek (sıralama deterministik; çeşitliliği Python'da yapacağız)
        pool = Recipe.search(dom, order="kcal desc, id asc", limit=limit)

        # Tekrarları ve yakın geçmiştekileri ele
        recent_ids = self._recent_recipe_ids(member, days=3)
        pool = [r for r in pool if r.id not in used_ids and r.id not in recent_ids]

        # Kiler uygunluğu
        if require_pantry:
            have_ids = set((member.pantry_product_ids or self.env['product.product']).ids)
            pool = [r for r in pool if self._pantry_ok(r, have_ids)]

        return pool

    def _pick_one(self, candidates, rng):
        """Havuzdan birini seç (Python Random ile)."""
        if not candidates:
            return False
        # küçük bir ağırlık: kcal'e yakın olanlara ufak öncelik verebilirsin
        idx = rng.randrange(0, len(candidates))
        return candidates[idx]


    def _auto_assign_workout(self):
        """Boşsa uygun bir antrenman ata (örnek: haftanın gününe göre)."""
        Workout = self.env["diet.workout"].sudo()
        for plan in self:
            if plan.workout_id:
                continue
            # Basit örnek: haftanın gününe göre seçim
            # 0=Mon ... 6=Sun
            wd = (plan.date or fields.Date.today()).weekday()
            dom = []
            # istersen zorluk/program filtreniz varsa buraya ekleyin
            # örn: dom += [('difficulty', '=', plan.member_id.program_id.pace)]
            w = Workout.search(dom, limit=1, order="id asc")
            if w:
                plan.workout_id = w.id

    # --- YENİ: Rastgele kayıt seçici (order="random()" yerine) ---
    def _random_recipe(self, base_domain=None, kcal_cap=None, exclude_ids=None):
        Recipe = self.env["diet.recipe"].sudo()
        dom = list(base_domain or [])
        if kcal_cap is not None:
            dom.append(("kcal", "<=", float(kcal_cap)))
        if exclude_ids:
            dom.append(("id", "not in", list(exclude_ids)))

        count = Recipe.search_count(dom)
        if not count:
            return Recipe.browse()
        offset = random.randint(0, count - 1)
        return Recipe.search(dom, limit=1, offset=offset, order="id")

    def generate_random_meals(self, max_total_kcal=2200, extra_max_kcal=1000):
        """En az 1 akşam yemeği, toplam ≤ max_total_kcal.
        Ek öğünler (kahvaltı/snack) ≤ extra_max_kcal ve toplam limiti aşmayacak."""
        Recipe = self.env["diet.recipe"].sudo()

        for plan in self:
            # Temizlik
            plan.meal_line_ids.sudo().unlink()
            total = 0.0
            used_ids = set()
            rng = Random(f"{plan.id}-{plan.date or ''}-{fields.Datetime.now()}")

            member = plan.member_id

            # 1) Zorunlu akşam yemeği (course='meal' öncelik)
            dinner_pool = self._candidate_pool(
                base_domain=[('course', '=', 'meal')],
                kcal_max=max_total_kcal,
                member=member,
                used_ids=used_ids,
                require_pantry=True,
                limit=200
            )
            # Kiler uyumlu hiç yoksa kiler şartını gevşet
            if not dinner_pool:
                dinner_pool = self._candidate_pool(
                    base_domain=[('course', '=', 'meal')],
                    kcal_max=max_total_kcal,
                    member=member,
                    used_ids=used_ids,
                    require_pantry=False,
                    limit=200
                )

            dinner = self._pick_one(dinner_pool, rng) if dinner_pool else False
            if not dinner:
                # Son çare: en düşük kalorili herhangi bir tarif
                dinner = Recipe.search([], order="kcal asc", limit=2)

            if dinner and (dinner.kcal or 0) <= max_total_kcal:
                self.env["diet.daily.meal.line"].sudo().create({
                    "plan_id": plan.id,
                    "meal_type": "dinner",
                    "recipe_id": dinner.id,
                })
                total += dinner.kcal or 0.0
                used_ids.add(dinner.id)

            # 2) Kalan kalori için kahvaltı/snack
            extra_types = ["breakfast", "snack"]
            idx = 0
            while total < max_total_kcal - 1:
                remain = max_total_kcal - total
                single_cap = min(extra_max_kcal, remain)

                # Önce kiler uyumlu havuz
                extra_pool = self._candidate_pool(
                    base_domain=[('kcal', '>=', 0)],  # course aşağıda atanacak
                    kcal_max=single_cap,
                    member=member,
                    used_ids=used_ids,
                    require_pantry=True,
                    limit=200
                )
                # course filtrelemesi: kahvaltı/snack için yan/ salata da kabul
                def _ok_for(meal_type, r):
                    if meal_type == "breakfast":
                        return r.course in ('meal', 'side', 'salad')
                    elif meal_type == "snack":
                        return r.course in ('side', 'salad')
                    return True

                mtype = extra_types[idx % len(extra_types)]
                extra_pool = [r for r in extra_pool if _ok_for(mtype, r)]

                # Kiler uyumlu yoksa şartı gevşet
                if not extra_pool:
                    extra_pool = self._candidate_pool(
                        base_domain=[],
                        kcal_max=single_cap,
                        member=member,
                        used_ids=used_ids,
                        require_pantry=False,
                        limit=200
                    )
                    extra_pool = [r for r in extra_pool if _ok_for(mtype, r)]

                rec = self._pick_one(extra_pool, rng) if extra_pool else False
                if not rec:
                    break  # ekleyecek uygun tarif bulunamadı

                self.env["diet.daily.meal.line"].sudo().create({
                    "plan_id": plan.id,
                    "meal_type": mtype,
                    "recipe_id": rec.id,
                })
                total += rec.kcal or 0.0
                used_ids.add(rec.id)
                idx += 1

            # Durum ve (varsa) spor ataması
            if hasattr(plan, "_auto_assign_workout"):
                plan._auto_assign_workout()
            plan.state = "ready"
        return True
    @api.model



    
    def _pick_recipe(self, kcal_target, meal_type="dinner", cheat=False):
        """Hedef kcal'e yakın tarif seç (rastgele offset)."""
        Recipe = self.env["diet.recipe"].sudo()
        if meal_type == "dinner":
            base_domain = [("course", "=", "meal")]
        elif meal_type == "breakfast":
            base_domain = [("course", "in", ["meal", "side", "salad"])]
        elif meal_type == "lunch":
            base_domain = [("course", "=", "meal")]
        else:  # snack
            base_domain = [("course", "in", ["side", "salad"])]

        if cheat:
            rec = self._random_recipe(base_domain + [("is_cheat", "=", True)])
            if rec:
                return rec

        window = 150
        for _ in range(6):  # 150 -> 450 -> ...
            dom = list(base_domain) + [
                ("kcal", ">=", max(0, kcal_target - window)),
                ("kcal", "<=", kcal_target + window),
            ]
            count = Recipe.search_count(dom)
            if count:
                offset = random.randint(0, count - 1)
                return Recipe.search(dom, limit=1, offset=offset, order="id")
            window += 300

        return Recipe.search(base_domain, limit=1, order="id")

    def generate_with_schema(self, meal_schema, target_kcal, cheat=False, seed=None):
        """Belirtilen öğün şemasına göre satırları üret."""
        for plan in self:
            plan.meal_line_ids.sudo().unlink()
            plan.target_kcal = int(target_kcal or 0)

            # oranlar: dinner zorunlu, diğerleri opsiyonel
            if len(meal_schema) == 2:   # dinner + (breakfast | lunch)
                ratios = {"dinner": 0.55}
            elif len(meal_schema) == 3: # dinner + biri + snack
                ratios = {"dinner": 0.50, "snack": 0.10}
            else:                       # dinner tek başına
                ratios = {"dinner": 1.0}

            for m in meal_schema:
                if m not in ratios:
                    ratios[m] = round((1.0 - sum(ratios.values())), 2)
            remain = max(0.0, 1.0 - sum(ratios.values()))
            if remain and "dinner" in ratios:
                ratios["dinner"] += remain

            # NOTE: Random(seed ...) kaldırıldı; zaten kullanılmıyordu
            for meal_type in meal_schema:
                kcal_goal = int(target_kcal * ratios[meal_type])
                recipe = plan._pick_recipe(kcal_goal, meal_type=meal_type, cheat=cheat)
                if recipe:
                    self.env["diet.daily.meal.line"].sudo().create({
                        "plan_id": plan.id,
                        "meal_type": meal_type,
                        "recipe_id": recipe.id,
                    })

    @api.depends("member_id", "program_id")
    def _compute_target(self):
        for rec in self:
            if not rec.member_id or not rec.program_id:
                rec.target_kcal = 0
                continue
            tdee = self._estimate_tdee(rec.member_id)
            deficit = floor((rec.program_id.deficit_min + rec.program_id.deficit_max) / 2)
            rec.target_kcal = max(800, floor(tdee - deficit))

    @api.depends("member_id", "date")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.member_id.partner_id.name or 'Ayse <3'} - {rec.date or ''}"

    def _estimate_tdee(self, member):
        if member.gender == "male":
            bmr = 10 * member.weight_kg + 6.25 * member.height_cm - 5 * member.age + 5
        else:
            bmr = 10 * member.weight_kg + 6.25 * member.height_cm - 5 * member.age - 161
        mult = {
            "sedentary": 1.2, "light": 1.375, "moderate": 1.55, "very": 1.725, "athlete": 1.9
        }.get(member.activity_level or "light", 1.375)
        return floor(bmr * mult)

    def action_generate_meals(self):
        for rec in self:
            rec.meal_line_ids.sudo().unlink()
            targets = {
                "breakfast": floor(rec.target_kcal * 0.25),
                "lunch":     floor(rec.target_kcal * 0.35),
                "dinner":    floor(rec.target_kcal * 0.30),
                "snack":     floor(rec.target_kcal * 0.10),
            }
            for where, kcal_target in targets.items():
                recipe = rec._find_recipe_for_target(kcal_target)
                status, used_recipe, msg = rec._check_pantry_or_alternative(recipe)
                self.env["diet.daily.meal.line"].sudo().create({
                    "plan_id": rec.id,
                    "meal_type": where,
                    "recipe_id": used_recipe.id if used_recipe else False,
                    "note": msg,
                    # burdaki değişken related & readonly, set etmiyoz o yüzden
                })
            rec.state = "ready"

    def _find_recipe_for_target(self, kcal_target, tolerance=120):
        Recipe = self.env["diet.recipe"]
        candidates = Recipe.search([
            ("kcal", ">=", max(0, kcal_target - tolerance)),
            ("kcal", "<=", kcal_target + tolerance),
        ], limit=1, order="id")
        if candidates:
            return candidates[0]
        simple = Recipe.search([("is_simple", "=", True)], limit=1, order="id")
        return simple or Recipe.search([], limit=1, order="id")

    def _check_pantry_or_alternative(self, recipe):
        member = self.member_id
        have_ids = set(member.pantry_product_ids.ids)
        if recipe and all(line.product_id.id in have_ids for line in recipe.line_ids):
            return ("ok", recipe, "Evdeki malzemeler mevcut.")

        simple = self.env["diet.recipe"].search([("is_simple", "=", True)], limit=1, order="id")
        if simple and all(l.product_id.id in have_ids for l in simple.line_ids):
            return ("alt", simple, f"Alternatif basit öğün önerildi: {simple.name}")

        missing = []
        if recipe:
            for l in recipe.line_ids:
                if l.product_id.id not in have_ids:
                    missing.append(l.product_id.display_name)
        msg = "Alternatif öğün bulunamadı. Ucuz olur: " + ", ".join(missing[:5])
        return ("missing", False, msg)


class DietDailyMealLine(models.Model):
    _name = "diet.daily.meal.line"
    _description = "Günlük Plan Öğünü"

    plan_id = fields.Many2one("diet.daily.plan", required=True, ondelete="cascade")
    meal_type = fields.Selection([
        ("breakfast", "Kahvaltı"),
        ("lunch", "Öğle"),
        ("dinner", "Akşam"),
        ("snack", "Ara Öğün"),
    ], string="Öğün", required=True)

    recipe_id = fields.Many2one("diet.recipe", string="Yemek")
    kcal = fields.Float("Kalori (kcal)", related="recipe_id.kcal", store=True, readonly=True)
    note = fields.Char("Not")

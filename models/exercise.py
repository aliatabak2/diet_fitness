from odoo import models, fields

class DietExercise(models.Model):
    _name = "diet.exercise"
    _description = "Spor Hareketi"

    name = fields.Char("Hareket", required=True)
    description = fields.Text("Açıklama")
    duration_min = fields.Integer("Süre (dk)")
    reps = fields.Integer("Tekrar")
    sets = fields.Integer("Set")
    #yaklaşık kalori (opsiyonellll)
    kcal_burn = fields.Integer("Yakılan Kalori (tahmini)")


class DietWorkout(models.Model):
    _name = "diet.workout"
    _description = "Spor Programı (Günlük)"
    name = fields.Char("Ad", required=True)
    difficulty = fields.Selection([
        ('easy','Kolay'), ('medium','Orta'), ('hard','Zor')
    ], string="Zorluk")
    duration_min = fields.Integer("Süre (dk)")
    description = fields.Text("Açıklama")
    kcal_burn = fields.Integer("Yakılan Kalori (tahmini)")
  
    line_ids = fields.One2many("diet.workout.line", "workout_id", string="Hareketler")


class DietWorkoutLine(models.Model):
    _name = "diet.workout.line"
    _description = "Spor Programı Satırı"
    name = fields.Char("Ad", required=True)
    workout_id = fields.Many2one("diet.workout", required=True, ondelete="cascade")
    exercise_id = fields.Many2one("diet.exercise", string="Hareket", required=True)
    duration_min = fields.Integer("Süre (dk)")
    reps = fields.Integer("Tekrar")
    sets = fields.Integer("Set")

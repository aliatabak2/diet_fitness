# -*- coding: utf-8 -*-
from odoo import models, fields

class DietForumMessage(models.Model):
    _name = "diet.forum.message"
    _description = "Diet Forum Chat Message"
    _order = "create_date desc"

    author_id = fields.Many2one(
        "res.partner",
        string="Author",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )
    body = fields.Text("Mesaj", required=True)

class DietForumPost(models.Model):
    _name = "diet.forum.post"
    _description = "Diet Forum Post"
    _order = "create_date desc"

    author_id = fields.Many2one(
        "res.partner",
        string="Author",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )
    title = fields.Char("Başlık", required=True)
    body = fields.Text("İçerik")  # Html yerine Text: bağımlılık riskini sıfırlar
    comment_ids = fields.One2many("diet.forum.comment", "post_id", string="Yorumlar")

class DietForumComment(models.Model):
    _name = "diet.forum.comment"
    _description = "Diet Forum Comment"
    _order = "create_date asc"

    post_id = fields.Many2one("diet.forum.post", string="Gönderi", required=True)
    author_id = fields.Many2one(
        "res.partner",
        string="Author",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )
    body = fields.Text("Yorum", required=True)

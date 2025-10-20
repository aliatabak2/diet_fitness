# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class DietForumPortal(http.Controller):

    # Forum ana sayfa: chat + gönderiler
    @http.route(['/my/diet/forum'], type='http', auth='user', website=True)
    def forum_home(self, **kw):
        Message = request.env['diet.forum.message'].sudo()
        Post = request.env['diet.forum.post'].sudo()
        messages = Message.search([], limit=50)  # son 50 mesaj
        posts = Post.search([], limit=20)
        return request.render('diet_fitness.portal_forum_home', {
            'messages': messages,
            'posts': posts,
        })

    # Chat’e mesaj gönder
    @http.route(['/my/diet/forum/chat/send'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def forum_chat_send(self, **post):
        body = (post.get('body') or '').strip()
        if body:
            request.env['diet.forum.message'].sudo().create({'body': body})
        return request.redirect('/my/diet/forum')

    # Yeni forum gönderisi oluştur
    @http.route(['/my/diet/forum/post/create'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def forum_post_create(self, **post):
        title = (post.get('title') or '').strip()
        body = post.get('body') or ''
        if title:
            new_post = request.env['diet.forum.post'].sudo().create({'title': title, 'body': body})
            return request.redirect(f"/my/diet/forum/post/{new_post.id}")
        return request.redirect('/my/diet/forum')

    # Gönderi detay
    @http.route(['/my/diet/forum/post/<int:post_id>'], type='http', auth='user', website=True)
    def forum_post_detail(self, post_id, **kw):
        post = request.env['diet.forum.post'].sudo().browse(post_id)
        if not post.exists():
            return request.redirect('/my/diet/forum')
        return request.render('diet_fitness.portal_forum_post', {
            'post': post,
        })

    # Yorum ekle
    @http.route(['/my/diet/forum/post/<int:post_id>/comment'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def forum_post_comment(self, post_id, **post):
        body = (post.get('body') or '').strip()
        if body:
            request.env['diet.forum.comment'].sudo().create({'post_id': post_id, 'body': body})
        return request.redirect(f"/my/diet/forum/post/{post_id}")

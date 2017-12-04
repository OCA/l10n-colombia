# -*- coding: utf-8 -*-
from odoo import http

# class BaseCity(http.Controller):
#     @http.route('/base_city/base_city/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_city/base_city/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_city.listing', {
#             'root': '/base_city/base_city',
#             'objects': http.request.env['base_city.base_city'].search([]),
#         })

#     @http.route('/base_city/base_city/objects/<model("base_city.base_city"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_city.object', {
#             'object': obj
#         })
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug
import logging
import pprint

from odoo import http, _
from odoo.http import request

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class AlsatpardakhtController(http.Controller):
    _redirectAddress = '/payment/alsatpardakht/accept'

    @staticmethod
    def alsatpardakht_validate_data(**get):
        """ alsatpardakht contacts using GET, at least for accept """
        _logger.info('Alasatpardakht: entering form_feedback with get data %s', pprint.pformat(get))  # debug
        RefId = get.get('iN')
        if get.get('Invoice'):
            RefId = get.get('Invoice')
        tx = None
        if RefId:
            tx = request.env['payment.transaction'].sudo().search([('alsatpardakht_refid', '=', RefId)])

        res = request.env['payment.transaction'].sudo().form_feedback(get, 'alsatpardakht')
        _logger.info('alsatpardakht: validated data')
        if not res and tx:
            tx._set_transaction_error(_('Validation error occured. Please contact your administrator.'))

        return res

    @http.route([_redirectAddress], type='http', auth='public', methods=['GET'], csrf=False, save_session=False)
    def alsatpardakht_form_feedback(self, **get):
        """
        The session cookie created by Odoo has not the attribute SameSite. Most of browsers will force this attribute
        with the value 'Lax'. After the payment, alsatpardakht will perform a GET request on this route. For all these
        reasons, the cookie won't be added to the request. As a result, if we want to save the session, the server will
        create a new session cookie. Therefore, the previous session and all related information will be lost, so it
        will lead to undesirable behaviors. This is the reason why `save_session=False` is needed.
        """
        _logger.info('Alsatpardakht IPN form_feedback with GET data %s', pprint.pformat(get))  # debug
        try:
            self.alsatpardakht_validate_data(**get)
        except ValidationError:
            _logger.exception('Unable to validate the alsatpardakht payment')

        return werkzeug.utils.redirect('/payment/process')

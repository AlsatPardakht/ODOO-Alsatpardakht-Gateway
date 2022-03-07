# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, http, _
from werkzeug import urls
from odoo.addons.payment_alsatpardakht.controllers.main import AlsatpardakhtController
import requests
import logging
from odoo.addons.payment.models.payment_acquirer import ValidationError
import json

_logger = logging.getLogger(__name__)


class AcquirerAlsatpardakht(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('alsatpardakht', 'Alsatpardakht')],
                                ondelete={'alsatpardakht': 'set default'})
    as_api_key = fields.Char(string="Api Key")
    # as_direct_gatway = fields.Char(string="Direct GetWay")
    as_direct_gatway = fields.Boolean(string="Direct GetWay",
                                      help="Use IPG interface")

    description = fields.Html(translate=True)

    _token = {
        "t": ""
    }

    def _get_alsatpardakht_urls(self, environment):
        """ Alsatpardakht URLS """
        if environment == 'prod':
            return {
                'alsatpardakht_sign_url': 'https://www.alsatpardakht.com/API_V1/sign.php',
                'alsatpardakht_go_url': 'https://www.alsatpardakht.com/API_V1/Go.php',
                'alsatpardakht_callback_url': 'https://www.alsatpardakht.com/API_V1/callback.php',
                'alsatpardakht_ipg_sign_url': 'https://www.alsatpardakht.com/IPGAPI/Api22/send.php',
                'alsatpardakht_ipg_go_url': 'https://www.alsatpardakht.com/IPGAPI/Api2/Go.php',
                'alsatpardakht_ipg_verify': 'https://www.alsatpardakht.com/IPGAPI/Api22/VerifyTransaction.php'
            }
        else:
            return {
                'alsatpardakht_sign_url': 'https://www.alsatpardakht.com/API_V1/sign.php',
                'alsatpardakht_go_url': 'https://www.alsatpardakht.com/API_V1/Go.php',
                'alsatpardakht_callback_url': 'https://www.alsatpardakht.com/API_V1/callback.php',
                'alsatpardakht_ipg_sign_url': 'https://www.alsatpardakht.com/IPGAPI/Api22/send.php',
                'alsatpardakht_ipg_go_url': 'https://www.alsatpardakht.com/IPGAPI/Api2/Go.php',
                'alsatpardakht_ipg_verify': 'https://www.alsatpardakht.com/IPGAPI/Api22/VerifyTransaction.php'
            }

    def _as_request(self, params=None, method=None, url=None, payload=None):
        if payload is not None:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'PHPSESSID=ldhfcra8jb3kicfoui7p1bo1a0'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            return response.text
        elif params is not None:
            params.update({
                'Api': self.as_api_key,
            })

            files = [

            ]
            headers = {
                'Cookie': 'PHPSESSID=1kpqgnv0to3n5qq2nk8ik7rmc4'
            }

            res = requests.request(method, url, headers=headers, data=params, files=files)

            response = res.text
            return response
        else:
            return None

    def alsatpardakht_get_sign_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        if self.as_direct_gatway:
            return self._get_alsatpardakht_urls(environment)['alsatpardakht_sign_url']
        else:
            return self._get_alsatpardakht_urls(environment)['alsatpardakht_ipg_sign_url']

    def alsatpardakht_get_verify_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        if self.as_direct_gatway:
            return self._get_alsatpardakht_urls(environment)['alsatpardakht_callback_url']
        else:
            return self._get_alsatpardakht_urls(environment)['alsatpardakht_ipg_verify']

    def sign_request(self, params={}):
        data = dict(
            InvoiceNumber=params['InvoiceNumber'],
            Amount=params['Amount'],
            RedirectAddress=params['RedirectAddress'],
            Api=self.as_api_key,
        )

        amount = str(params['Amount'])
        payload = "ApiKey=" + self.as_api_key + "&Amount=" + str(amount) + "&Tashim=%5B%5D&RedirectAddressPage=" + \
                  params['RedirectAddress'] + "?Invoice=" + str(params['InvoiceNumber'])

        sign_link = self.alsatpardakht_get_sign_url()

        if self.as_direct_gatway:
            res = self._as_request(data, 'POST', sign_link)
        else:
            res = self._as_request(method='POST', url=sign_link, payload=payload)

        return res

    def callback_request(self, params):
        verify_link = self.alsatpardakht_get_verify_url()
        payload = {'iN': params.get('iN', ''),
                   'iD': params.get('iD', ''),
                   'tref': params.get('tref', ''),
                   'Api': self.as_api_key}
        return self._as_request(params=None, method='POST', url=verify_link, payload=payload)

    def alsatpardakht_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        alsatpardakht_tx_values = dict(values)

        order_reference = values.get('reference')

        # additionalData = _('Customer Info: partner_id (%s), partner_name (%s)') % (
        #     values.get('partner_id'), values.get('partner_name'))

        transaction = self.env['payment.transaction'].search(
            [('reference', '=', order_reference), ('state', '=', 'draft')], limit=1)

        currency_obj = values.get('currency')
        amount_value = int(values.get('amount'))

        if currency_obj.name == 'IRR':
            amount = amount_value
        elif currency_obj.name == 'IRT':
            amount = amount_value * 10
        else:
            error_msg = 'Currency: data error: Invalid Currency'
            _logger.info(error_msg)  # debug
            raise ValidationError(error_msg)

        data = {
            'InvoiceNumber': transaction.id,
            'Amount': amount,
            'RedirectAddress': urls.url_join(base_url, AlsatpardakhtController._redirectAddress),
            'Api': self.as_api_key,
        }
        # Pay Request Method Call
        result = self.sign_request(data)
        if result is not None:
            result = json.loads(result)

            if result['IsSuccess'] and result['IsSuccess'] == 1 and result['Token'] is not None:
                Token = result['Token']
                self._token.update({'t': Token})
                temp_alsatpardakht_tx_values = {'RefId': transaction.id}
                alsatpardakht_tx_values.update(temp_alsatpardakht_tx_values)
                self.env['payment.transaction'].sudo()._alsatpardakht_set_tx_RefId(values.get('reference'),
                                                                                   transaction.id)
            else:
                if self.as_direct_gatway:
                    error_msg = _('Alsatpardakht: feedback error: Transaction Approved')
                else:
                    error_msg = result['Message']
                _logger.info(error_msg)  # debug
                raise ValidationError(error_msg)
        else:
            error_msg = _('Alsatpardakht: feedback error: Sign request failed')
            _logger.info(error_msg)  # debug
            raise ValidationError(error_msg)

        return alsatpardakht_tx_values

    def alsatpardakht_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        pay_token = self._token
        if self.as_direct_gatway:
            return self._get_alsatpardakht_urls(environment)[
                       'alsatpardakht_go_url'] + "?Token=" + pay_token['t']
        else:
            return self._get_alsatpardakht_urls(environment)[
                       'alsatpardakht_ipg_go_url'] + "?Token=" + pay_token['t']


class PaymentTxAlsatpardakht(models.Model):
    _inherit = 'payment.transaction'

    alsatpardakht_refid = fields.Char(string='alsatpardakht Reference Id', readonly=True,
                                      help='Reference of the TX as stored in the acquirer database')

    @api.model
    def _alsatpardakht_set_tx_RefId(self, reference, RefId):
        tx = self.search([('reference', '=', reference)])
        if tx:
            tx.alsatpardakht_refid = RefId
        return

    def _alsatpardakht_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        RefId = data.get('iN')
        if data.get('Invoice'):
            RefId = data.get('Invoice')
        if self.alsatpardakht_refid and RefId.upper() != self.alsatpardakht_refid.upper():
            invalid_parameters.append(('RefId', RefId, self.alsatpardakht_refid))
        return invalid_parameters

    def form_feedback(self, data, acquirer_name):
        if data.get('tref') and acquirer_name == 'alsatpardakht':
            # transaction = self.env['payment.transaction'].search([('reference', '=', data.get('tref'))])
            RefId = data.get('iN')
            if data.get('Invoice'):
                RefId = data.get('Invoice')
            data.update({
                'ref_id': RefId
            })
            # url = 'payment_intents/%s' % transaction.stripe_payment_intent
            # resp = transaction.acquirer_id._stripe_request(url)
            # if resp.get('charges') and resp.get('charges').get('total_count'):
            #     resp = resp.get('charges').get('data')[0]
            #
            # data.update(resp)
            # _logger.info('Stripe: entering form_feedback with post data %s' % pprint.pformat(data))
        return super(PaymentTxAlsatpardakht, self).form_feedback(data, acquirer_name)

    @api.model
    def _alsatpardakht_form_get_tx_from_data(self, data):
        """ Given a data dict coming from alsatpardakht, verify it and
        find the related transaction record. """
        RefId = data.get('tref', '')
        InvoiceDate = data.get('iD', '')
        InvoiceNumber = data.get('iN', '')
        if data.get('Invoice'):
            InvoiceNumber = data.get('Invoice')

        if not InvoiceDate or not InvoiceNumber or not RefId:
            error_msg = 'Alsatpardakht: received data with missing InvoiceDate (%s) or RefId (%s) or InvoiceNumber (%s)' % (
                InvoiceDate, RefId, InvoiceNumber)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.env['payment.transaction'].search([('alsatpardakht_refid', '=', InvoiceNumber)])
        if not tx or len(tx) > 1:
            error_msg = 'Alsatpardakht: received data for reference %s' % RefId
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _alsatpardakht_form_validate(self, data):
        status = data.get('tref', None)
        InvoiceDate = data.get('iD', '')
        InvoiceNumber = data.get('iN', '')
        RefId = data.get('tref', '')

        former_tx_state = self.state

        date = fields.date.today()
        res = {}

        if status:
            alsatpardakht_acquirer_obj = self.env['payment.acquirer'].search([('provider', '=', 'alsatpardakht')])
            data = {
                'tref': int(RefId),
                'iN': InvoiceNumber,
                'iD': InvoiceDate,
                'Api': alsatpardakht_acquirer_obj.as_api_key,
            }

            result = alsatpardakht_acquirer_obj.callback_request(data)
            result = json.loads(result)
            try:
                if result['PSP'] and result['VERIFY']:
                    psp_isSuccess = result['PSP']['IsSuccess']
                    verify_isSuccess = result['VERIFY']['IsSuccess']
                    if psp_isSuccess and verify_isSuccess:
                        self.acquirer_reference = RefId
                        res.update(date=date)
                        self._set_transaction_done()
                        if self.state == 'done' and self.state != former_tx_state:
                            _logger.info('Validated Alsatpardakht payment for tx %s: set as done' % self.reference)
                            return self.write(res)
                        return True
            except Exception as e:
                _logger.exception(str(e))

        if status is not None:
            error = _('%s Transaction Error: (%s) %s') % (self.reference, status, 0)
        else:
            error = _('Received unrecognized status for Alsatpardakht payment ') + self.reference

        self._set_transaction_error(error)
        return True

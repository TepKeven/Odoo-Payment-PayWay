# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging, requests


from werkzeug import urls
from datetime import datetime

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_payway import const
from odoo.addons.payment_payway.controllers.main import PayWayController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return PayWay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        def get_language_code(lang_):
            """ Return the language code corresponding to the provided lang.

            If the lang is not mapped to any language code, the country code is used instead. In
            case the country code has no match either, we fall back to English.

            :param str lang_: The lang, in IETF language tag format.
            :return: The corresponding language code.
            :rtype: str
            """
            language_code_ = const.LANGUAGE_CODES_MAPPING.get(lang_)
            if not language_code_:
                country_code_ = lang_.split('_')[0]
                language_code_ = const.LANGUAGE_CODES_MAPPING.get(country_code_)
            if not language_code_:
                language_code_ = const.LANGUAGE_CODES_MAPPING['en']
            return language_code_

        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payway':
            return res

        base_url = self.provider_id.get_base_url()
        # The lang is taken from the context rather than from the partner because it is not required
        # to be logged in to make a payment, and because the lang is not always set on the partner.
        # lang = self._context.get('lang') or 'en_US'
        partner_first_name, partner_last_name = payment_utils.split_partner_name(self.partner_name)
        rendering_values = {
            'api_url': self.provider_id._payway_get_api_url() + "/api/payment-gateway/v1/payments/purchase",
            'req_time': datetime.now().strftime('%Y%m%d%H%M%S'),
            'merchant_id': self.provider_id.payway_merchant_id,
            'tran_id': self.id, 
            'firstname': partner_first_name,
            'lastname': partner_last_name,
            'email': self.partner_email,
            'amount': self.amount,
            'payment_option': const.PAYMENT_METHODS_MAPPING[self.payment_method_id.code],
            'return_url': urls.url_join(base_url, PayWayController._webhook_url),
            'currency': self.provider_id.available_currency_ids[0].name,
            'cancel_url': urls.url_join(base_url, PayWayController._checkout_return_url),
            'continue_success_url': urls.url_join(base_url, PayWayController._checkout_return_url),
        }
        rendering_values.update({
            'secure_hash': self.provider_id._payway_calculate_payment_secure_hash(
                rendering_values
            )
        })

        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of `payment` to find the transaction based on PayWay data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data are received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payway' or len(tx) == 1:
            return tx

        tran_id = notification_data.get('tran_id')

        if not tran_id:
            raise ValidationError(
                "PayWay: " + _("Received data with missing tran_id %(tran_id)s.", tran_id=tran_id)
            )

        tx = self.search([('id', '=', tran_id), ('provider_code', '=', 'payway')])
        if not tx:
            raise ValidationError(
                "PayWay: " + _("No transaction found matching id %s.", tran_id)
            )

        return tx

    def _process_notification_data(self, notification_data):
        """ Override of `payment' to process the transaction based on PayWay data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payway':
            return

        # Verify transaction status from ABA with webhook data using webhook tran_id
        post_data = {
            "req_time": datetime.now().strftime('%Y%m%d%H%M%S'),
            'merchant_id': self.provider_id.payway_merchant_id,
            'tran_id': notification_data.get('tran_id'), 
        }

        post_data.update({
            'hash': self.provider_id._payway_calculate_check_txn_secure_hash(
                post_data
            )
        })

        response = requests.post(self.provider_id._payway_get_api_url() + "/api/payment-gateway/v1/payments/check-transaction-2", data=post_data)
        response_data = response.json()

        status_code = response_data['status']['code']
        status_msg = response_data['status']['message']
        if status_code != '00':
            _logger.warning(
                "Verify ABA transaction with the following errors: %s: %s and "
                "reference %s.", status_code, status_msg, self.reference
            )
            self._set_error("PayWay: " + _("Error code: %s, message: %s", status_code, status_msg))
            return 

        payment_code = int(response_data['data']['payment_status_code'])

        # Update the provider reference.
        self.provider_reference = response_data['data']['apv']

        if payment_code == 0:
            self._set_done()
        elif payment_code in list(const.STATUS_CODE_MAPPING.keys()):
            payment_msg = response_data['data']['payment_status'] or const.STATUS_CODE_MAPPING[payment_code]
            if payment_code in (1,2):
                self._set_pending(_(
                    "Your payment is being processed with (payment code %s; message = %s; "
                    "payway reference %s)", payment_code, payment_msg, self.provider_reference
                ))
            else:
                self._set_error(_(
                    "An error occurred during the processing of your payment (payment code %s; message = %s; "
                    "payway reference %s). Please try again.", payment_code, payment_msg, self.provider_reference
                ))
        else:
            _logger.warning(
                "Received data with invalid payment code (%s) for transaction with "
                "reference %s.", payment_code, self.reference
            )
            self._set_error("PayWay: " + _("Unknown payment code: %s", payment_code))

# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_payway import const


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('payway', "ABA PayWay")], ondelete={'payway': 'set default'}
    )
    payway_merchant_id = fields.Char(
        string="PayWay Merchant ID",
        help="The Merchant ID solely used to identify your PayWay account.",
        required_if_provider='payway',
    )
    payway_public_key = fields.Char(
        string="PayWay public key",
        required_if_provider='payway',
        groups='base.group_system',
    )

    @api.depends('code')
    def _compute_view_configuration_fields(self):
        """ Override of payment to make the `available_currency_ids` field required.

        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'payway').update({
            'require_currency': True,
        })

    # ==== CONSTRAINT METHODS ===#

    @api.constrains('available_currency_ids', 'state')
    def _limit_available_currency_ids(self):
        for provider in self.filtered(lambda p: p.code == 'payway'):
            if len(provider.available_currency_ids) > 1 and provider.state != 'disabled':
                raise ValidationError(_("Only one currency can be selected by PayWay account."))

    # === BUSINESS METHODS ===#

    def _payway_get_api_url(self):
        """ Return the URL of the API corresponding to the provider's state.

        :return: The API URL.
        :rtype: str
        """
        self.ensure_one()

        environment = 'production' if self.state == 'enabled' else 'sandbox'
        api_url = const.API_URLS[environment]
        return api_url

    def _payway_calculate_payment_secure_hash(self, data):
        """ Compute the secure hash for the provided data according to the PayWay documentation.

        :param dict data: The data to hash.
        :return: The calculated hash.
        :rtype: str
        """
        secure_hash_keys = const.PAYMENT_SECURE_HASH_KEYS
        data_to_sign = [str(data[k]) for k in secure_hash_keys] 
        signing_string = ''.join(data_to_sign)
        hmac_hash = hmac.new(self.payway_public_key.encode(), signing_string.encode(), hashlib.sha512).digest()
        base64_encoded = base64.b64encode(hmac_hash).decode()
        return base64_encoded
    
    def _payway_calculate_check_txn_secure_hash(self, data):
        """ Compute the secure hash for the provided data according to the PayWay documentation for checking transaction.

        :param dict data: The data to hash.
        :return: The calculated hash.
        :rtype: str
        """
        secure_hash_keys = const.CHECK_TXN_SECURE_HASH_KEYS
        data_to_sign = [str(data[k]) for k in secure_hash_keys] 
        signing_string = ''.join(data_to_sign)
        hmac_hash = hmac.new(self.payway_public_key.encode(), signing_string.encode(), hashlib.sha512).digest()
        base64_encoded = base64.b64encode(hmac_hash).decode()
        return base64_encoded

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'payway':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES

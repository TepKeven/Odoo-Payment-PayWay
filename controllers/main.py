# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class PayWayController(http.Controller):
    _checkout_return_url = '/payment/payway/return'
    _webhook_url = '/payment/payway/webhook'

    @http.route(_checkout_return_url, type='http', auth='public', methods=['GET'])
    def payway_return_from_checkout(self, **data):
        """ Process the notification data sent by PayWay after redirection.

        :param dict data: The notification data.
        """
        # Don't process the notification data as they contain no valuable information except for the
        # reference and PayWay doesn't expose an endpoint to fetch the data from the API.
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def payway_webhook(self, **data):
        """ Process the notification data sent by PayWay to the webhook.

        :param dict data: The notification data.
        :return: The 'OK' string to acknowledge the notification.
        :rtype: str
        """
        _logger.info("Notification received from PayWay with data:\n%s", pprint.pformat(data))
        try:
            # Check the integrity of the notification data.
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'payway', data
            )
            # self._verify_notification_signature(data, tx_sudo)

            # Handle the notification data.
            tx_sudo._handle_notification_data('payway', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Unable to handle the notification data; skipping to acknowledge.")

        return 'OK'  # PayWay does not really have acknowledgement of webhook request. I just put it here just in case. 

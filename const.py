# Part of Odoo. See LICENSE file for full copyright and licensing details.

API_URLS = {
    'production': 'https://checkout.payway.com.kh',
    'sandbox': 'https://checkout-sandbox.payway.com.kh'
}

# The codes of the payment methods to activate when PayWay is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    'card',
    'abapay',
    'bakong',
]

# Mapping of payment method codes to PayWay codes.
PAYMENT_METHODS_MAPPING = {
    'card': 'cards',
    'abapay': 'abapay',
    'bakong': 'bakong'
}

# The keys of the values to use in the calculation of the payment secure hash.
PAYMENT_SECURE_HASH_KEYS = [
    'req_time',
    'merchant_id',
    'tran_id',
    'amount',
    'firstname',
    'lastname',
    'email',
    'payment_option',
    'return_url',
    'cancel_url',
    'continue_success_url',
    'currency',
]

# The keys of the values to use in the calculation of the check txn secure hash.
CHECK_TXN_SECURE_HASH_KEYS = [
    'req_time',
    'merchant_id',
    'tran_id'
]

# PayWay status code and their meaning.
STATUS_CODE_MAPPING = {
    0: "Approved", 
    1: "Created",
    2: "Pending",
    3: "Declined",
    4: "Refunded",
    5: "Wrong Hash",
    6: "tran_id not Found",
    11: "Other Server side Error",
}

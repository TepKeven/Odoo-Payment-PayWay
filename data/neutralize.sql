-- disable payway payment provider
UPDATE payment_provider
   SET payway_merchant_id = NULL,
       payway_public_key = NULL,

# Billing Worker TLS Certificate Rotation

Rotate the billing worker's TLS certificate when the `BillingCertExpiring` alert fires. The certificate is valid for 90 days. The alert fires 14 days before expiry.

## Prerequisites

- You have VPN access and the `billing-ops` role in Vault.
- Do not rotate the certificate during month-end close (the first 3 business days of the month). The billing worker stops picking up invoices while drained.

## Steps

1. Issue the new certificate:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

   Save the output to `/etc/billing/tls/new.pem`.

2. Back up the current certificate:

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

3. Drain the billing worker:

   ```
   billingctl drain --wait 120
   ```

   This takes up to 2 minutes.

4. Swap the certificates:

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. Restart the billing worker:

   ```
   sudo systemctl restart billing-worker
   ```

6. Verify the certificate is loaded:

   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   The response must be `ok`. If it is not, roll back to the previous certificate:

   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   sudo systemctl restart billing-worker
   ```

7. Resume the billing worker:

   ```
   billingctl resume
   ```

## Questions

Ping #billing-oncall on Slack.

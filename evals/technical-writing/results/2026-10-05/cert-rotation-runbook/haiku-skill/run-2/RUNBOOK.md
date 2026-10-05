# Rotate the billing worker TLS certificate

Use this runbook when the `BillingCertExpiring` alert fires (14 days before expiry). The certificate is valid for 90 days.

## Before you start

- Connect to the VPN.
- Verify you have the `billing-ops` role in Vault. If Vault rejects your request, you lack this role.
- Do not rotate during the month-end close (the first 3 business days of the month). The billing worker does not pick up new invoices while drained.

## Rotate the certificate

1. Issue the new certificate:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

   Save the output to `/etc/billing/tls/new.pem`.

2. Back up the current certificate:

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

3. Drain the billing worker (takes up to 2 minutes):

   ```
   billingctl drain --wait 120
   ```

4. Swap the certificate:

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. Restart the billing-worker service:

   ```
   sudo systemctl restart billing-worker
   ```

6. Verify the service is healthy:

   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   You should see `ok`. If you see an error, go to [Roll back the certificate](#roll-back-the-certificate).

7. Resume the billing worker:

   ```
   billingctl resume
   ```

## Roll back the certificate

If the health check fails after restart:

```
sudo mv /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
sudo systemctl restart billing-worker
curl -s https://billing.internal.example.com:8443/healthz
```

Verify you see `ok`.

## Get help

Post in #billing-oncall.

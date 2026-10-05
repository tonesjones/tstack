# Billing Worker Cert Rotation Runbook

Rotate the TLS certificate for the billing worker when the BillingCertExpiring alert fires (14 days before expiry). The certificate is valid for 90 days.

## Prerequisites

- You have VPN access.
- You have the `billing-ops` Vault role.
- Avoid this procedure during the first 3 business days of each month (month-end close period). The billing worker stops picking up new invoices when drained.

## Procedure

1. Issue a new certificate and save it:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h > /tmp/new-cert.json
   cat /tmp/new-cert.json | jq -r '.data.certificate' > /etc/billing/tls/new.pem
   ```

2. Drain the worker to stop processing invoices:

   ```
   billingctl drain --wait 120
   ```

   This takes up to 2 minutes. Wait for the command to return.

3. Back up the current certificate:

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

4. Replace the certificate:

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. Restart the billing worker:

   ```
   sudo systemctl restart billing-worker
   ```

6. Verify the service is running:

   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   You should see `ok`. If you see an error, go to the rollback section.

7. Resume processing invoices:

   ```
   billingctl resume
   ```

## Rollback

If the healthz check fails, restore the previous certificate and restart:

```
sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
sudo systemctl restart billing-worker
billingctl resume
```

## Questions

Ping #billing-oncall.

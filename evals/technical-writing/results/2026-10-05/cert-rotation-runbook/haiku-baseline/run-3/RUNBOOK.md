# Billing Worker Certificate Rotation Runbook

Rotate the billing worker's TLS certificate when the BillingCertExpiring alert fires (14 days before expiry). The certificate is valid for 90 days.

## Prerequisites

- VPN access
- `billing-ops` role in Vault
- SSH access to billing hosts

## Do Not Rotate During

- First 3 business days of the month (month-end close period)
- The worker will not accept new invoices during draining

## Procedure

1. **Verify prerequisites**
   ```
   vault login
   ```
   If authentication fails, you lack the `billing-ops` role.

2. **Generate new certificate**
   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```
   Save the output to `/etc/billing/tls/new.pem`.

3. **Backup current certificate**
   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

4. **Drain the worker**
   ```
   billingctl drain --wait 120
   ```
   This can take up to 2 minutes. The worker will not pick up new invoices during this time.

5. **Swap certificate**
   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

6. **Restart the service**
   ```
   sudo systemctl restart billing-worker
   ```

7. **Verify health**
   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```
   Expected response: `ok`

8. **Resume draining**
   ```
   billingctl resume
   ```

## Troubleshooting

**Health check returns error instead of `ok`:**

1. Restore the previous certificate:
   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   ```

2. Restart the service:
   ```
   sudo systemctl restart billing-worker
   ```

3. Verify health returns to `ok`:
   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

4. Contact #billing-oncall for assistance.

## Support

For questions, reach out to #billing-oncall.

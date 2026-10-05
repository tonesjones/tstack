# Billing Worker Cert Rotation Runbook

Rotate the TLS cert for the billing worker (systemd unit `billing-worker`).

**When to use:** the `BillingCertExpiring` alert fires. Certs are valid for 90 days, and the alert fires 14 days before expiry.

**Questions?** Ask in #billing-oncall.

## Before you start

- [ ] **Check the date.** Do not run this during month-end close (the first 3 business days of the month). Draining stops the job runner from picking up new invoices. You have 14 days from the alert, so wait until close is over.
- [ ] Be on the VPN.
- [ ] Have the `billing-ops` role. Without it, Vault rejects your requests.

## Procedure

1. **Issue the new cert.** Save the output to `/etc/billing/tls/new.pem`, because later steps use it.

   ```bash
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

2. **Drain the consumer.** This can take up to 2 minutes. The job runner stops picking up new invoices until you resume.

   ```bash
   billingctl drain --wait 120
   ```

3. **Back up the current cert.** Do this before the swap. Rollback depends on it.

   ```bash
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

4. **Swap in the new cert.**

   ```bash
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. **Restart the service.**

   ```bash
   sudo systemctl restart billing-worker
   ```

6. **Verify health.** The command must print `ok`.

   ```bash
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   If it does not print `ok`, go to [Rollback](#rollback).

7. **Resume the consumer.**

   ```bash
   billingctl resume
   ```

## Rollback

Use this if the health check in step 6 fails.

1. Restore the old cert:

   ```bash
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   ```

2. Restart and re-check health:

   ```bash
   sudo systemctl restart billing-worker
   curl -s https://billing.internal.example.com:8443/healthz
   ```

3. Once health returns `ok`, run `billingctl resume`.
4. If it still fails, escalate in #billing-oncall.

## Background

Certs were rotated by hand on each box until 2024. Issuance now goes through Vault, so only the install steps above are manual.

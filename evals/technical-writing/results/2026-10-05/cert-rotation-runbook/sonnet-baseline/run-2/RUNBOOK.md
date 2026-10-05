# Billing Worker Cert Rotation Runbook

Rotate the TLS certificate for the billing worker. Use this when the `BillingCertExpiring` alert fires.

- Certs are valid for 90 days. The alert fires 14 days before expiry.
- Certs are issued by Vault (automated since 2024).
- The "billing worker" and the systemd unit `billing-worker` are the same service.

## Before you start

1. **Check the date.** Do not run this during month-end close (the first 3 business days of the month). Draining stops the job runner from picking up new invoices. If the cert expires before close ends, ask in #billing-oncall first.
2. **Connect to the VPN** and make sure you have the `billing-ops` role. Without both, Vault rejects you.

## Procedure

1. **Issue the new cert.**

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

   Save the output to `/etc/billing/tls/new.pem`. You need it in step 4.

2. **Drain the consumer.** This can take up to 2 minutes. Invoice processing is paused until step 6.

   ```
   billingctl drain --wait 120
   ```

3. **Back up the current cert.** Do this before the swap. Rollback depends on it.

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

4. **Swap in the new cert.**

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. **Restart the service and check health.**

   ```
   sudo systemctl restart billing-worker
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   Expected output: `ok`. If you get anything else, go to [Rollback](#rollback).

6. **Resume the consumer.**

   ```
   billingctl resume
   ```

## Rollback

Use this if the health check in step 5 does not return `ok`.

1. Restore the old cert:

   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   sudo systemctl restart billing-worker
   ```

2. Re-run the health check from step 5. It should return `ok`.
3. Run `billingctl resume` so invoices are processed again.
4. Ask in #billing-oncall for help with the failed rotation. The old cert is still close to expiry.

## Help

Ask in #billing-oncall.

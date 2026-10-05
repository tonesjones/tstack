# How to rotate the billing worker TLS certificate

Use this runbook when the `BillingCertExpiring` alert fires. The alert fires 14 days before the certificate expires. Each certificate is valid for 90 days.

The billing worker is the `billing-worker` service in systemd. Vault issues the certificate.

## Before you start

- Do not rotate during month-end close, which is the first 3 business days of the month. While the worker is drained, it stops picking up new invoices. If the alert fires during close, wait until close ends. You have 14 days of margin.
- Connect to the VPN.
- Make sure you have the `billing-ops` role. Without it, Vault rejects your requests.

## Rotate the certificate

1. Issue a new certificate:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

2. Save the output to `/etc/billing/tls/new.pem`.

3. Drain the consumer. The command waits up to 120 seconds, so expect it to take up to 2 minutes.

   ```
   billingctl drain --wait 120
   ```

4. Back up the current certificate. Do this before the swap, because the rollback needs it.

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

5. Swap in the new certificate:

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

6. Restart the service:

   ```
   sudo systemctl restart billing-worker
   ```

7. Check the health endpoint:

   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   If the response is `ok`, go to the next step. If it is anything else, follow [Roll back](#roll-back).

8. Resume the consumer:

   ```
   billingctl resume
   ```

## Roll back

If the health check in step 7 fails, restore the previous certificate.

1. Restore the backup:

   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   ```

2. Restart the service:

   ```
   sudo systemctl restart billing-worker
   ```

3. Run the health check from step 7 again. The response must be `ok`.

4. Resume the consumer with `billingctl resume`.

5. Ask for help in #billing-oncall. The old certificate is still close to expiry.

## Get help

Ask in #billing-oncall.

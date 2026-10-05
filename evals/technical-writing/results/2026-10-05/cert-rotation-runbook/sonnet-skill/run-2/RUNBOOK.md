# How to rotate the billing worker TLS certificate

Follow this runbook when the `BillingCertExpiring` alert fires. The alert fires 14 days before the certificate expires. Each certificate is valid for 90 days.

The billing worker is the `billing-worker` service in systemd.

## Before you start

- Do not rotate during the month-end close, which is the first 3 business days of the month. Draining stops the job runner from picking up new invoices. If the certificate expires before the close ends, ask in #billing-oncall first.
- Connect to the VPN.
- Make sure you have the `billing-ops` role. Without it, Vault rejects your requests.

## Rotate the certificate

1. Issue a new certificate:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

2. Save the certificate from the output to `/etc/billing/tls/new.pem`.

3. Drain the consumer. The command waits up to 120 seconds.

   ```
   billingctl drain --wait 120
   ```

4. Back up the current certificate. You need the backup to roll back.

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

5. Put the new certificate in place:

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

   The expected output is `ok`. If the output is anything else, go to [Roll back](#roll-back).

8. Resume the consumer:

   ```
   billingctl resume
   ```

## Roll back

If the health check in step 7 does not return `ok`, restore the previous certificate.

1. Restore the backup:

   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   ```

2. Restart the service:

   ```
   sudo systemctl restart billing-worker
   ```

3. Run the health check from step 7 again. The expected output is `ok`.

4. Resume the consumer with `billingctl resume`.

5. Post the failed output in #billing-oncall.

## Get help

Ask in #billing-oncall.

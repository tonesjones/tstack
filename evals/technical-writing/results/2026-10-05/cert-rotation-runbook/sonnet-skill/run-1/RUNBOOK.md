# How to rotate the billing worker TLS certificate

Use this procedure when the `BillingCertExpiring` alert fires. The alert fires 14 days before the certificate expires. Each certificate is valid for 90 days (`ttl=2160h`).

The billing worker is the `billing-worker` service in systemd.

## Before you start

- Do not rotate during the month-end close, which is the first 3 business days of the month. Draining stops the job runner from picking up new invoices.
- Connect to the VPN.
- Make sure you have the `billing-ops` role. Without it, Vault rejects the request.

## Rotate the certificate

1. Issue the new certificate, and save the output to `/etc/billing/tls/new.pem`:

   ```
   vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
   ```

2. Drain the consumer. The command waits up to 2 minutes:

   ```
   billingctl drain --wait 120
   ```

3. Copy the current certificate to `previous.pem`. You need this copy to roll back.

   ```
   sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
   ```

4. Replace the current certificate with the new one:

   ```
   sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
   ```

5. Restart the service:

   ```
   sudo systemctl restart billing-worker
   ```

6. Check the health endpoint:

   ```
   curl -s https://billing.internal.example.com:8443/healthz
   ```

   The expected output is `ok`. If the output is anything else, go to [Roll back](#roll-back).

7. Resume the consumer:

   ```
   billingctl resume
   ```

## Roll back

If the health check in step 6 does not return `ok`, restore the previous certificate:

1. Copy `previous.pem` over `current.pem`:

   ```
   sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
   ```

2. Restart the service:

   ```
   sudo systemctl restart billing-worker
   ```

3. Run the health check from step 6 again. When it returns `ok`, run `billingctl resume`.

If the health check still fails, ask for help in #billing-oncall.

## Get help

Ask in #billing-oncall.

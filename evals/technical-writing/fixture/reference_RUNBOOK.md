# Rotate the billing-worker TLS certificate

The billing-worker certificate is valid for 90 days. The `BillingCertExpiring` alert fires 14 days before it expires. Vault issues the certificate.

Don't rotate during the month-end close (the first 3 business days of the month). While billing-worker is drained, it stops picking up new invoices.

## Before you start

- Connect to the VPN.
- Get the `billing-ops` role. Without it, Vault rejects the request.

## Rotate the certificate

1. Issue a new certificate and save the output to `/etc/billing/tls/new.pem`:
   `vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h`
2. Drain billing-worker. This takes up to 2 minutes:
   `billingctl drain --wait 120`
3. Back up the current certificate:
   `sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem`
4. Swap in the new certificate:
   `sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem`
5. Restart the service:
   `sudo systemctl restart billing-worker`
6. Check that the health endpoint returns `ok`:
   `curl -s https://billing.internal.example.com:8443/healthz`
7. If the health check doesn't return `ok`, restore `/etc/billing/tls/previous.pem` to `/etc/billing/tls/current.pem` and restart the service again.
8. Resume billing-worker:
   `billingctl resume`

## Background

Rotation was manual on each host until 2024, when the team moved certificate issuance to Vault.

Questions go to #billing-oncall.

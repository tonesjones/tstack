# Billing Worker TLS Certificate Rotation Runbook

## Overview
Rotate the TLS certificate for the billing worker service. Certificates are valid for 90 days; the `BillingCertExpiring` alert fires 14 days before expiry.

## Prerequisites
- VPN access
- `billing-ops` Vault role
- SSH access to billing worker host
- **Do not perform during month-end close** (first 3 business days of the month) — the service will stop processing new invoices while drained

## Procedure

### 1. Verify Prerequisites
```
vault auth list  # Confirm you can reach Vault
```

### 2. Request New Certificate
```
vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
```
Copy the entire certificate output and save to `/etc/billing/tls/new.pem`.

### 3. Backup Current Certificate
```
sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
```

### 4. Drain Consumer
```
billingctl drain --wait 120
```
This halts new invoice processing and waits up to 2 minutes for in-flight jobs to complete.

### 5. Swap Certificate
```
sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
```

### 6. Restart Service
```
sudo systemctl restart billing-worker
```

### 7. Verify Health
```
curl -s https://billing.internal.example.com:8443/healthz
```
Expected response: `ok`

If the response is not `ok`, proceed to **Rollback**.

### 8. Resume Consumer
```
billingctl resume
```

## Rollback
If health check fails:
```
sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
sudo systemctl restart billing-worker
curl -s https://billing.internal.example.com:8443/healthz
```

## Support
Questions or issues: `#billing-oncall` Slack channel

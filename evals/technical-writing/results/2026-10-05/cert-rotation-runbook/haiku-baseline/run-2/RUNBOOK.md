# Billing Worker TLS Certificate Rotation

## Overview

Rotate the TLS certificate for the billing worker. Certificates are valid for 90 days. The alert `BillingCertExpiring` fires 14 days before expiry.

## Prerequisites

- Connected to the VPN
- Have the `billing-ops` role in Vault
- Not during month-end close (first 3 business days of the month)

## Steps

### 1. Issue new certificate from Vault

```
vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h > /etc/billing/tls/new.pem
```

### 2. Back up current certificate

```
sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
```

### 3. Drain incoming jobs

```
billingctl drain --wait 120
```

This stops the worker from picking up new invoices. Allow up to 2 minutes for existing jobs to complete.

### 4. Swap certificates

```
sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
```

### 5. Restart the service

```
sudo systemctl restart billing-worker
```

### 6. Verify health check passes

```
curl -s https://billing.internal.example.com:8443/healthz
```

Expected output: `ok`

### 7. Resume job processing

```
billingctl resume
```

## Rollback

If the health check fails in step 6, roll back immediately:

```
sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
sudo systemctl restart billing-worker
curl -s https://billing.internal.example.com:8443/healthz
```

Then restart the drain and investigate the issue.

## Support

Post questions in #billing-oncall

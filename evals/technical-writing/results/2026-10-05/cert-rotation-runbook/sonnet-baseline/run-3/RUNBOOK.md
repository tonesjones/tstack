# Billing Worker Cert Rotation Runbook

Rotate the TLS certificate for the billing worker (the `billing-worker` systemd service).

**When to use:** the `BillingCertExpiring` alert fires. It fires 14 days before expiry. Certs are valid for 90 days and are issued by Vault.

**Expected duration:** about 10 minutes. The drain step can take up to 2 minutes.

## Before you start

1. **Check the date. Do not rotate during month-end close** (the first 3 business days of the month). Draining stops the job runner from picking up new invoices. If the alert fires during close, you have 14 days of runway, so wait until close ends.
2. Connect to the VPN.
3. Confirm you have the `billing-ops` role. Without it, Vault rejects the request in step 1.

## Procedure

### 1. Issue the new cert

```bash
vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h
```

Save the output to `/etc/billing/tls/new.pem`. You need this file in step 4.

### 2. Drain the consumer

```bash
billingctl drain --wait 120
```

This can take up to 2 minutes. The job runner stops picking up new invoices until you resume in step 6.

### 3. Back up the current cert

```bash
sudo cp /etc/billing/tls/current.pem /etc/billing/tls/previous.pem
```

Do this before the swap. The rollback depends on it.

### 4. Swap in the new cert

```bash
sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem
```

### 5. Restart and verify

```bash
sudo systemctl restart billing-worker
curl -s https://billing.internal.example.com:8443/healthz
```

The curl must print `ok`. If it does, continue to step 6. If it prints anything else, go to [Rollback](#rollback).

### 6. Resume the consumer

```bash
billingctl resume
```

Rotation is done.

## Rollback

Use this if the health check in step 5 does not return `ok`.

```bash
sudo cp /etc/billing/tls/previous.pem /etc/billing/tls/current.pem
sudo systemctl restart billing-worker
curl -s https://billing.internal.example.com:8443/healthz   # expect: ok
billingctl resume
```

Then ask in #billing-oncall before retrying. The old cert is still close to expiry, so don't leave the rollback in place.

## Help

Ask in #billing-oncall.

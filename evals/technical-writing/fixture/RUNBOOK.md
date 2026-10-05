# Billing Worker Cert Rotation Runbook

So basically this doc is about how to rotate the TLS cert for the billing worker. Some history: we used to do this by hand on each box but in 2024 we moved to Vault so now its mostly automated, which is nice. The certificate is valid for 90 days and the alert (BillingCertExpiring) fires 14 days before expiry.

Steps

- first you should make sure you are on the VPN and have the `billing-ops` role, otherwise vault will reject you.
- The new cert is issued by running `vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h` and the output should be saved to /etc/billing/tls/new.pem (it'll be needed later).
- then the consumer needs to be drained, which you can do with `billingctl drain --wait 120`. this can take up to 2 minutes. Note that the job runner will stop picking up new invoices while its drained so dont do this during the month-end close (first 3 business days of the month)!!
- swap the cert: `sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem`
- restart the service using `sudo systemctl restart billing-worker` and then check `curl -s https://billing.internal.example.com:8443/healthz` returns `ok`. If it doesn't, roll back by restoring /etc/billing/tls/previous.pem - actually you should copy current.pem to previous.pem before the swap step, I forgot to mention that.
- Undrain with `billingctl resume`.

Also, it's important to note that the worker is the same thing as billing-worker in systemd.

Questions? Ping #billing-oncall

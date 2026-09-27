# Nocturnix WPForms Bridge v1.0.1

Fixes:
- Uses `/api/integrations/wpforms/intake` for real submissions.
- Uses `GET /health` for the admin connection test.
- Sends the Repair Platform request model exactly as:
  `form_id`, `entry_id`, `fields`.
- Uses WPForms form 608 as the default enabled form.
The enabled form IDs can be overridden in wp-config.php with NOCTURNIX_WPFORMS_BRIDGE_ENABLED_FORM_IDS using a comma-separated list, for example: 608,1162.

Required `wp-config.php` values:

```php
define('NOCTURNIX_API_BASE_URL', 'https://api.nocturnixrepair.com');
define('NOCTURNIX_WPFORMS_WEBHOOK_SECRET', 'yNQI2fw1ckPoko0MXOFNS6Jb2H2ZbbQROdu1v0m6LUQ');
```

The optional endpoint override may remain if already present:

```php
define(
    'NOCTURNIX_WPFORMS_API_ENDPOINT',
    'https://api.nocturnixrepair.com/api/integrations/wpforms/intake'
);
```

<?php
if (!defined('ABSPATH')) { exit; }

final class Nocturnix_API_Client {
    private const TIMEOUT = 20;

    public static function base_url(): string {
        return defined('NOCTURNIX_API_BASE_URL')
            ? untrailingslashit(esc_url_raw((string) NOCTURNIX_API_BASE_URL))
            : '';
    }

    public static function intake_endpoint(): string {
        if (defined('NOCTURNIX_WPFORMS_API_ENDPOINT')) {
            return esc_url_raw((string) NOCTURNIX_WPFORMS_API_ENDPOINT);
        }
        $base = self::base_url();
        return $base === '' ? '' : $base . '/api/integrations/wpforms/intake';
    }

    public static function health_endpoint(): string {
        $base = self::base_url();
        return $base === '' ? '' : $base . '/health';
    }

    public static function secret_configured(): bool {
        return defined('NOCTURNIX_WPFORMS_WEBHOOK_SECRET')
            && trim((string) NOCTURNIX_WPFORMS_WEBHOOK_SECRET) !== '';
    }

    public static function send_intake(array $payload): array|WP_Error {
        if (!self::secret_configured()) {
            return new WP_Error('nocturnix_missing_secret', 'Nocturnix webhook secret is not configured.');
        }
        $endpoint = self::intake_endpoint();
        if ($endpoint === '') {
            return new WP_Error('nocturnix_missing_endpoint', 'Nocturnix WPForms intake endpoint is not configured.');
        }

        return self::normalize(wp_remote_post($endpoint, array(
            'timeout' => self::TIMEOUT,
            'redirection' => 0,
            'headers' => array(
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
                'User-Agent' => 'Nocturnix-WPForms-Bridge/' . NOCTURNIX_WPFORMS_BRIDGE_VERSION,
                'X-Nocturnix-Webhook-Secret' => (string) NOCTURNIX_WPFORMS_WEBHOOK_SECRET,
            ),
            'body' => wp_json_encode($payload),
            'data_format' => 'body',
        )));
    }

    public static function test_connection(): array|WP_Error {
        $endpoint = self::health_endpoint();
        if ($endpoint === '') {
            return new WP_Error('nocturnix_missing_base_url', 'Nocturnix API base URL is not configured.');
        }

        return self::normalize(wp_remote_get($endpoint, array(
            'timeout' => self::TIMEOUT,
            'redirection' => 0,
            'headers' => array(
                'Accept' => 'application/json',
                'User-Agent' => 'Nocturnix-WPForms-Bridge/' . NOCTURNIX_WPFORMS_BRIDGE_VERSION,
            ),
        )));
    }

    private static function normalize(array|WP_Error $response): array|WP_Error {
        if (is_wp_error($response)) { return $response; }
        $status = (int) wp_remote_retrieve_response_code($response);
        $body = (string) wp_remote_retrieve_body($response);
        $decoded = json_decode($body, true);
        $body = is_array($decoded) ? $decoded : $body;

        if ($status < 200 || $status >= 300) {
            return new WP_Error(
                'nocturnix_api_http_error',
                sprintf('Nocturnix API returned HTTP %d.', $status),
                array('status' => $status, 'body' => $body)
            );
        }
        return array('status' => $status, 'body' => $body);
    }
}

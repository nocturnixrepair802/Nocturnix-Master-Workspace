<?php
if (!defined('ABSPATH')) { exit; }

final class Nocturnix_Logger {
    public static function log(
        string $level,
        string $message,
        array $context = array()
    ): void {
        $bridge_debug = defined('NOCTURNIX_WPFORMS_BRIDGE_DEBUG')
            && NOCTURNIX_WPFORMS_BRIDGE_DEBUG;

        $wordpress_debug = defined('WP_DEBUG')
            && WP_DEBUG;

        if (!$bridge_debug && !$wordpress_debug) {
            return;
        }

        foreach (
            array(
                'secret',
                'token',
                'password',
                'api_key',
                'authorization',
                'x-nocturnix-webhook-secret'
            )
            as $key
        ) {
            if (array_key_exists($key, $context)) {
                $context[$key] = '[REDACTED]';
            }
        }

        $line =
            '[Nocturnix WPForms Bridge] [' .
            strtoupper($level) .
            '] ' .
            $message;

        if ($context) {
            $line .= ' ' . wp_json_encode(
                $context,
                JSON_UNESCAPED_SLASHES
            );
        }

        error_log($line);
    }
}
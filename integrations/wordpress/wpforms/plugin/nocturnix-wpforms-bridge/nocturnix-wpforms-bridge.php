<?php
/**
 * Plugin Name: Nocturnix WPForms Bridge
 * Description: Securely forwards approved WPForms repair intake submissions to the Nocturnix Repair Platform API.
 * Version: 1.0.3
 * Author: Nocturnix Repair
 * Requires at least: 6.0
 * Requires PHP: 8.0
 */
if (!defined('ABSPATH')) { exit; }

define('NOCTURNIX_WPFORMS_BRIDGE_VERSION', '1.0.3');
define('NOCTURNIX_WPFORMS_BRIDGE_DEBUG', false);
define('NOCTURNIX_WPFORMS_BRIDGE_DIR', plugin_dir_path(__FILE__));
if ( ! defined( 'NOCTURNIX_WPFORMS_BRIDGE_ENABLED_FORM_ID' ) ) {
    define( 'NOCTURNIX_WPFORMS_BRIDGE_ENABLED_FORM_ID', 608 );
}

require_once NOCTURNIX_WPFORMS_BRIDGE_DIR . 'includes/class-nocturnix-logger.php';
require_once NOCTURNIX_WPFORMS_BRIDGE_DIR . 'includes/class-nocturnix-api-client.php';
require_once NOCTURNIX_WPFORMS_BRIDGE_DIR . 'includes/class-nocturnix-wpforms-handler.php';
require_once NOCTURNIX_WPFORMS_BRIDGE_DIR . 'admin/class-nocturnix-admin.php';

add_action('plugins_loaded', function (): void {
    Nocturnix_WPForms_Handler::init();

    if (is_admin()) {
        Nocturnix_Admin::init();
    }
});
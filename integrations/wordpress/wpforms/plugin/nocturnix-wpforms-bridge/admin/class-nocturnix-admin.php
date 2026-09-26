<?php
if (!defined('ABSPATH')) { exit; }

final class Nocturnix_Admin {
    public static function init(): void {
        add_action(
            'admin_menu',
            array(__CLASS__, 'register_page')
        );

        add_action(
            'admin_post_nocturnix_test_connection',
            array(__CLASS__, 'test_connection')
        );
    }

    public static function register_page(): void {
        add_management_page(
            'Nocturnix WPForms Bridge',
            'Nocturnix WPForms Bridge',
            'manage_options',
            'nocturnix-wpforms-bridge',
            array(__CLASS__, 'render_page')
        );
    }

    public static function render_page(): void {
        if (!current_user_can('manage_options')) {
            return;
        }

        $notice = isset($_GET['nocturnix_notice'])
            ? sanitize_text_field(
                wp_unslash($_GET['nocturnix_notice'])
            )
            : '';

        $last_event = get_option(
            'nocturnix_wpforms_bridge_last_event',
            array()
        );
        ?>

        <div class="wrap">

            <h1>Nocturnix WPForms Bridge</h1>

            <?php if ($notice !== '') : ?>

                <div class="notice notice-info is-dismissible">
                    <p>
                        <?php echo esc_html($notice); ?>
                    </p>
                </div>

            <?php endif; ?>

            <table
                class="widefat striped"
                style="max-width:1000px"
            >
                <tbody>

                    <tr>
                        <th style="width:240px">
                            Bridge version
                        </th>
                        <td>
                            <?php
                            echo esc_html(
                                NOCTURNIX_WPFORMS_BRIDGE_VERSION
                            );
                            ?>
                        </td>
                    </tr>

                    <tr>
                        <th>
                            Enabled WPForms form
                        </th>
                        <td>
                            <?php
                            echo esc_html(
                                (string)
                                NOCTURNIX_WPFORMS_BRIDGE_ENABLED_FORM_ID
                            );
                            ?>
                        </td>
                    </tr>

                    <tr>
                        <th>
                            API base URL
                        </th>
                        <td>
                            <code>
                                <?php
                                echo esc_html(
                                    Nocturnix_API_Client::base_url()
                                );
                                ?>
                            </code>
                        </td>
                    </tr>

                    <tr>
                        <th>
                            WPForms intake endpoint
                        </th>
                        <td>
                            <code>
                                <?php
                                echo esc_html(
                                    Nocturnix_API_Client::intake_endpoint()
                                );
                                ?>
                            </code>
                        </td>
                    </tr>

                    <tr>
                        <th>
                            Health endpoint
                        </th>
                        <td>
                            <code>
                                <?php
                                echo esc_html(
                                    Nocturnix_API_Client::health_endpoint()
                                );
                                ?>
                            </code>
                        </td>
                    </tr>

                    <tr>
                        <th>
                            Webhook secret
                        </th>
                        <td>
                            <?php
                            echo Nocturnix_API_Client::secret_configured()
                                ? 'Configured'
                                : 'Not configured';
                            ?>
                        </td>
                    </tr>

                </tbody>
            </table>

            <h2>Last Bridge Event</h2>

            <p>
                This diagnostic shows the most recent WPForms
                event processed by the Nocturnix bridge.
                Submitted form fields and the webhook secret are
                not displayed here.
            </p>

            <?php if (empty($last_event)) : ?>

                <p>
                    No WPForms bridge event has been recorded yet.
                </p>

            <?php else : ?>

                <pre style="
                    max-width:1000px;
                    padding:16px;
                    background:#ffffff;
                    border:1px solid #ccd0d4;
                    overflow:auto;
                    white-space:pre-wrap;
                    word-break:break-word;
                "><?php
                    echo esc_html(
                        wp_json_encode(
                            $last_event,
                            JSON_PRETTY_PRINT |
                            JSON_UNESCAPED_SLASHES
                        )
                    );
                ?></pre>

            <?php endif; ?>

            <h2>Connection test</h2>

            <p>
                This performs a GET request to
                <code>/health</code>
                and does not create an intake record.
            </p>

            <form
                action="<?php echo esc_url(
                    admin_url('admin-post.php')
                ); ?>"
                method="post"
            >

                <input
                    type="hidden"
                    name="action"
                    value="nocturnix_test_connection"
                >

                <?php
                wp_nonce_field(
                    'nocturnix_test_connection'
                );

                submit_button(
                    'Test Nocturnix API Connection'
                );
                ?>

            </form>

        </div>

        <?php
    }

    public static function test_connection(): void {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.');
        }

        check_admin_referer(
            'nocturnix_test_connection'
        );

        $result =
            Nocturnix_API_Client::test_connection();

        $message = is_wp_error($result)
            ? 'Connection test failed: ' .
                $result->get_error_message()
            : 'Connection test passed. Nocturnix API health check returned HTTP ' .
                (int) ($result['status'] ?? 0) .
                '.';

        wp_safe_redirect(
            add_query_arg(
                array(
                    'page' =>
                        'nocturnix-wpforms-bridge',
                    'nocturnix_notice' =>
                        $message,
                ),
                admin_url('tools.php')
            )
        );

        exit;
    }
}
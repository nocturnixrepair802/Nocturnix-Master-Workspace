<?php
if (!defined('ABSPATH')) { exit; }

final class Nocturnix_WPForms_Handler {
    private const LAST_EVENT_OPTION = 'nocturnix_wpforms_bridge_last_event';

    public static function init(): void {
        add_action(
            'wpforms_process_complete',
            array(__CLASS__, 'handle_submission'),
            20,
            4
        );
    }

    public static function handle_submission(
        array $fields,
        array $entry,
        array $form_data,
        int $entry_id
    ): void {
        $form_id = isset($form_data['id'])
            ? (int) $form_data['id']
            : 0;

        self::record_event(
            'handler_fired',
            array(
                'form_id' => $form_id,
                'entry_id' => $entry_id,
                'enabled_form_ids' => $enabled_form_ids,
                'timestamp' => current_time('mysql', true),
            )
        );
            $enabled_form_ids = array_filter(
                array_map(
                    'intval',
                    explode(
                        ',',
                        (string) NOCTURNIX_WPFORMS_BRIDGE_ENABLED_FORM_IDS
                    )
                )
            );

            self::record_event(
                'handler_fired',
                array(
                    'form_id' => $form_id,
                    'entry_id' => $entry_id,
                    'enabled_form_ids' => $enabled_form_ids,
                    'timestamp' => current_time('mysql', true),
                )
            );

            if (!in_array($form_id, $enabled_form_ids, true)) {
                self::record_event(
                    'form_skipped',
                    array(
                        'form_id' => $form_id,
                        'entry_id' => $entry_id,
                        'enabled_form_ids' => $enabled_form_ids,
                        'timestamp' => current_time('mysql', true),
                    )
                );

                return;
            }


        $payload = array(
            'form_id' => (string) $form_id,
            'entry_id' => (string) $entry_id,
            'fields' => $fields,
        );

        $result = Nocturnix_API_Client::send_intake($payload);

        if (is_wp_error($result)) {
            $error_data = $result->get_error_data();

            self::record_event(
                'forward_failed',
                array(
                    'form_id' => $form_id,
                    'entry_id' => $entry_id,
                    'error_code' => $result->get_error_code(),
                    'error_message' => $result->get_error_message(),
                    'error_data' => is_array($error_data)
                        ? $error_data
                        : array(),
                    'timestamp' => current_time('mysql', true),
                )
            );

            Nocturnix_Logger::log(
                'error',
                'WPForms submission could not be forwarded.',
                array(
                    'form_id' => $form_id,
                    'entry_id' => $entry_id,
                    'error' => $result->get_error_message(),
                )
            );

            return;
        }

        self::record_event(
            'forward_success',
            array(
                'form_id' => $form_id,
                'entry_id' => $entry_id,
                'status' => $result['status'] ?? null,
                'body' => $result['body'] ?? null,
                'timestamp' => current_time('mysql', true),
            )
        );

        Nocturnix_Logger::log(
            'info',
            'WPForms submission forwarded successfully.',
            array(
                'form_id' => $form_id,
                'entry_id' => $entry_id,
                'status' => $result['status'] ?? null,
            )
        );
    }

    private static function record_event(
        string $event,
        array $data
    ): void {
        update_option(
            self::LAST_EVENT_OPTION,
            array(
                'event' => $event,
                'data' => $data,
            ),
            false
        );
    }
}
<?php
$CONFIG = array (
 'datadirectory' => '{{ app_data_dir }}',
 'log_type' => 'syslog',
 'logfile' => '',
 'integrity.check.disabled' => true,
 'apps_paths' => array(
 	array(
 		'path'=> '{{ app_dir }}/nextcloud/apps',
 		'url' => '/apps',
 		'writable' => false,
 	),
 	array(
 		'path'=> '{{ app_data_dir }}/extra-apps',
 		'url' => '/extra-apps',
 		'writable' => true,
 	),
 ),
); 
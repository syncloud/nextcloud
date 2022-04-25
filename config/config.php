<?php
$CONFIG = array (
 'datadirectory' => '{{ common_dir }}',
 'check_data_directory_permissions' => false,
 'log_type' => 'syslog',
 'logfile' => '',
 'apps_paths' => array(
 	array(
 		'path'=> '{{ app_dir }}/nextcloud/apps',
 		'url' => '/apps',
 		'writable' => false,
 	),
 	array(
 		'path'=> '{{ app_dir }}/nextcloud/extra-apps',
 		'url' => '/extra-apps',
 		'writable' => true,
 	),
 ),
); 

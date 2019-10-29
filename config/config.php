<?php
$CONFIG = array (
 'datadirectory' => '{{ common_dir }}',
 'log_type' => 'syslog',
 'logfile' => '',
 'apps_paths' => array(
 	array(
 		'path'=> '{{ app_dir }}/nextcloud/apps',
 		'url' => '/apps',
 		'writable' => false,
 	),
 	array(
 		'path'=> '{{ data_dir }}/extra-apps',
 		'url' => '/extra-apps',
 		'writable' => true,
 	),
 ),
); 

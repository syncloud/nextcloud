<?php
$CONFIG = array (
 'datadirectory' => '{{ app_data_dir }}',
 'log_type' => 'syslog',
 'logfile' => '',
 'integrity.check.disabled' => true,
 'mail_smtpmode' => 'smtp',
 'mail_smtphost' => 'localhost:25',
 "mail_smtpsecure" => '', 
 "mail_smtpauth" => false,
 "mail_smtpname" => "",
 "mail_smtppassword" => "",
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
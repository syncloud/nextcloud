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
 'enable_previews' => true,
 'enabledPreviewProviders' =>
  array (
    'OC\Preview\Movie',
    'OC\Preview\PNG',
    'OC\Preview\JPEG',
    'OC\Preview\GIF',
    'OC\Preview\BMP',
    'OC\Preview\XBitmap',
    'OC\Preview\MP3',
    'OC\Preview\MP4',
    'OC\Preview\TXT',
    'OC\Preview\MarkDown',
    'OC\Preview\PDF'
  ),
  'bulkupload.enabled' => false,
  'memcache.local' => '\OC\Memcache\APCu',
  'memcache.distributed' => '\OC\Memcache\Redis',
  'memcache.locking' => '\OC\Memcache\Redis',
  'redis' => [
   'host'     => '/var/snap/nextcloud/current/redis.sock',
   'port'     => 0,
  ],
  'maintenance_window_start' => 1,
);

<?php
require_once dirname(__FILE__).'/../nextcloud/lib/base.php';

if ($argc <= 2) {
    echo("usage: ".$argv[0]." key value1 [value2] [value3] ...\n");
    exit(1);
}

if ($argc == 3) {
    $value = $argv[2];
    if ($value === 'true')
      $value = true;
    if ($value === 'false')
      $value = false;
} else
    $value = array_slice($argv, 2);

echo("setting ".$argv[1]." = ".print_r($value, true)."\n");

try {
    $config = \OCP\Server::get(\OCP\IConfig::class);
    $config->setSystemValue($argv[1], $value);
    $written = $config->getSystemValue($argv[1]);
} catch (\Throwable $e) {
    fwrite(STDERR, "failed to set ".$argv[1].": ".$e->getMessage()."\n");
    exit(1);
}

if ($written != $value) {
    fwrite(STDERR, "wrote ".$argv[1]." but read back ".print_r($written, true)."\n");
    exit(1);
}

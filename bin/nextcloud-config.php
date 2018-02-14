<?php
require_once dirname(__FILE__).'/../nextcloud/lib/base.php';

if ($argc > 2) {
    if ($argc == 3) {
        $value = $argv[2];
        if ($value === 'true')
          $value = true;
        if ($value === 'false')
          $value = false;
    } else
        $value = array_slice($argv, 2);
    echo("setting ".$argv[1]." = ".print_r($value, true)."\n");
    \OC::$server->getConfig()->setSystemValue($argv[1], $value);
} else {
    echo("usage: ".$argv[0]." key value1 [value2] [value3] ...\n");
    exit(1);
}

package installer

import (
	"fmt"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/google/uuid"
	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const (
	App        = "nextcloud"
	UserName   = "nextcloud"
	DbName     = "nextcloud"
	DbUser     = "nextcloud"
	DbPassword = "nextcloud"
	PsqlPort   = 5436
	LogPath    = "log/nextcloud.log"

	SignalingSecretsFile = "signaling.secrets"
)

type Variables struct {
	AppDir                   string
	CommonDir                string
	DataDir                  string
	DbPsqlPort               int
	DatabaseDir              string
	ConfigDir                string
	Domain                   string
	SignalingSessionHashkey  string
	SignalingSessionBlockkey string
	SignalingInternalSecret  string
	SignalingBackendSecret   string
}

type Installer struct {
	appDir              string
	commonDir           string
	dataDir             string
	configDir           string
	extraAppsDir        string
	ncConfigPath        string
	ncConfigFile        string
	signalingSecretsPath string
	platformClient      *platform.Client
	executor            *Executor
	database            *Database
	occ                 *OCConsole
	ocConfig            *OCConfig
	cron                *Cron
	logger              *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	configDir := path.Join(dataDir, "config")
	executor := NewExecutor(logger)
	return &Installer{
		appDir:               appDir,
		commonDir:            commonDir,
		dataDir:              dataDir,
		configDir:            configDir,
		extraAppsDir:         path.Join(dataDir, "extra-apps"),
		ncConfigPath:         path.Join(dataDir, "nextcloud", "config"),
		ncConfigFile:         path.Join(dataDir, "nextcloud", "config", "config.php"),
		signalingSecretsPath: path.Join(dataDir, SignalingSecretsFile),
		platformClient:       platform.New(),
		executor:             executor,
		database:             NewDatabase(appDir, dataDir, configDir, DbUser, PsqlPort, executor, logger),
		occ:                  NewOCConsole(appDir, executor, logger),
		ocConfig:             NewOCConfig(appDir, executor, logger),
		cron:                 NewCron(UserName, executor, logger),
		logger:               logger,
	}
}

func (i *Installer) installConfig() error {
	if err := linux.CreateUser(UserName); err != nil {
		return err
	}

	if _, err := i.platformClient.InitStorage(App, UserName); err != nil {
		return err
	}

	secrets, err := loadOrCreateSignalingSecrets(i.signalingSecretsPath)
	if err != nil {
		return err
	}

	domain, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}

	variables := Variables{
		AppDir:                   i.appDir,
		CommonDir:                i.commonDir,
		DataDir:                  i.dataDir,
		DbPsqlPort:               PsqlPort,
		DatabaseDir:              i.database.DatabaseDir(),
		ConfigDir:                i.configDir,
		Domain:                   domain,
		SignalingSessionHashkey:  secrets.SessionHashkey,
		SignalingSessionBlockkey: secrets.SessionBlockkey,
		SignalingInternalSecret:  secrets.InternalSecret,
		SignalingBackendSecret:   secrets.BackendSecret,
	}

	if err := config.Generate(path.Join(i.appDir, "config"), i.configDir, variables); err != nil {
		return err
	}

	for _, dir := range []string{
		i.ncConfigPath,
		path.Join(i.commonDir, "log"),
		path.Join(i.commonDir, "nginx"),
		i.extraAppsDir,
	} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return err
		}
	}

	return i.fixPermissions()
}

func (i *Installer) Install() error {
	if err := i.installConfig(); err != nil {
		return err
	}

	defaultConfig := path.Join(i.configDir, "config.php")
	if err := copyFile(defaultConfig, i.ncConfigFile); err != nil {
		return err
	}
	if err := i.fixConfigPermission(); err != nil {
		return err
	}

	if err := i.database.Init(); err != nil {
		return err
	}
	return i.database.InitConfig()
}

func (i *Installer) PreRefresh() error {
	return i.database.Backup()
}

func (i *Installer) PostRefresh() error {
	if err := i.installConfig(); err != nil {
		return err
	}
	if err := i.migrateNextcloudConfig(); err != nil {
		return err
	}
	if err := i.fixVersionSpecificDbHost(); err != nil {
		return err
	}
	if err := i.database.Remove(); err != nil {
		return err
	}
	if err := i.database.Init(); err != nil {
		return err
	}
	return i.database.InitConfig()
}

func (i *Installer) Configure() error {
	if i.installed() {
		if err := i.upgrade(); err != nil {
			return err
		}
	} else {
		if err := i.initialize(); err != nil {
			return err
		}
	}

	storageDir, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}

	if _, err := i.occ.Run("ldap:set-config", "s01", "ldapEmailAttribute", "mail"); err != nil {
		return err
	}
	if _, err := i.occ.Run("config:system:set", "apps_paths", "1", "path", "--value="+i.extraAppsDir); err != nil {
		return err
	}
	if _, err := i.occ.Run("config:system:set", "dbhost", "--value="+i.database.DatabaseHost()); err != nil {
		return err
	}

	if err := i.cron.Remove(); err != nil {
		return err
	}
	if err := i.cron.Create(); err != nil {
		return err
	}

	for _, args := range [][]string{
		{"config:system:set", "memcache.local", "--value=\\OC\\Memcache\\APCu"},
		{"config:system:set", "redis", "host", "--value=/var/snap/nextcloud/current/redis.sock"},
		{"config:system:set", "redis", "port", "--value=0"},
		{"config:system:set", "memcache.distributed", "--value=\\OC\\Memcache\\Redis"},
		{"config:system:set", "memcache.locking", "--value=\\OC\\Memcache\\Redis"},
		{"config:system:set", "maintenance_window_start", "--value=1"},
	} {
		if _, err := i.occ.Run(args...); err != nil {
			return err
		}
	}

	if err := i.ocConfig.SetValue("loglevel", "2"); err != nil {
		return err
	}
	if err := i.ocConfig.SetValue("logfile", path.Join(i.commonDir, LogPath)); err != nil {
		return err
	}
	realStorage, err := filepath.EvalSymlinks(storageDir)
	if err != nil {
		realStorage = storageDir
	}
	if err := i.ocConfig.SetValue("datadirectory", realStorage); err != nil {
		return err
	}
	if err := i.ocConfig.SetValue("mail_smtpmode", "smtp"); err != nil {
		return err
	}
	if err := i.ocConfig.SetValue("mail_smtphost", "localhost:25"); err != nil {
		return err
	}
	if err := i.ocConfig.SetValue("mail_smtpauth", "false"); err != nil {
		return err
	}

	if _, err := i.occ.Run("app:disable", "logreader"); err != nil {
		return err
	}
	if _, err := i.occ.Run("app:disable", "app_api"); err != nil {
		return err
	}
	if err := i.AccessChange(); err != nil {
		return err
	}
	if _, err := i.occ.Run("maintenance:repair"); err != nil {
		return err
	}
	return i.fixPermissions()
}

func (i *Installer) PostStartRepair() error {
	i.logger.Info("post-start-repair")
	if !i.installed() {
		i.logger.Info("nextcloud not installed yet, skipping repair")
		return nil
	}
	if _, err := i.occ.Run("maintenance:repair"); err != nil {
		i.logger.Error("post-start repair failed; continuing", zap.Error(err))
	}
	if _, err := i.occ.Run("ldap:promote-group", "syncloud", "-y"); err != nil {
		i.logger.Error("post-start ldap promote-group failed; continuing", zap.Error(err))
	}
	return nil
}

func (i *Installer) StorageChange() error {
	if _, err := i.platformClient.InitStorage(App, UserName); err != nil {
		return err
	}
	if err := i.prepareStorage(); err != nil {
		return err
	}
	if _, err := i.occ.Run("config:system:delete", "instanceid"); err != nil {
		return err
	}
	if _, err := i.executor.Run("systemctl", "restart", "snap."+App+".php-fpm.service"); err != nil {
		return err
	}
	_, err := i.executor.Run("systemctl", "restart", "snap."+App+".nginx.service")
	return err
}

func (i *Installer) AccessChange() error {
	domain, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}
	out, err := exec.Command("hostname", "-I").Output()
	if err != nil {
		return err
	}
	localIP := strings.Fields(string(out))
	if len(localIP) == 0 {
		localIP = []string{""}
	}
	if err := i.ocConfig.SetValue("trusted_domains", "localhost", localIP[0], domain); err != nil {
		return err
	}
	if err := i.ocConfig.SetValue("trusted_proxies", "127.0.0.1", localIP[0]); err != nil {
		return err
	}
	return i.ocConfig.SetValue("overwrite.cli.url", "https://"+domain)
}

func (i *Installer) BackupPreStop() error {
	return i.PreRefresh()
}

func (i *Installer) RestorePreStart() error {
	return i.PostRefresh()
}

func (i *Installer) RestorePostStart() error {
	return i.Configure()
}

func (i *Installer) installed() bool {
	data, err := os.ReadFile(i.ncConfigFile)
	if err != nil {
		return false
	}
	return strings.Contains(string(data), "installed")
}

func (i *Installer) upgrade() error {
	if err := i.database.Restore(); err != nil {
		return err
	}
	if err := i.prepareStorage(); err != nil {
		return err
	}
	status, err := i.occ.Run("status")
	if err != nil {
		return err
	}
	i.logger.Info("status", zap.String("status", status))
	i.logger.Info("upgrading nextcloud")
	if _, err := i.occ.Run("upgrade"); err != nil {
		return err
	}
	if _, err := i.occ.Run("maintenance:mode", "--off"); err != nil {
		return err
	}
	if _, err := i.occ.Run("db:add-missing-indices"); err != nil {
		return err
	}
	if _, err := i.occ.Run("db:add-missing-columns"); err != nil {
		return err
	}
	if _, err := i.occ.Run("db:add-missing-primary-keys"); err != nil {
		return err
	}
	if err := i.database.Execute(DbName, "UPDATE oc_ldap_group_mapping SET owncloud_name='syncloud' WHERE owncloud_name='admin' AND ldap_dn ILIKE 'cn=syncloud,%';"); err != nil {
		return err
	}
	_, err = i.occ.Run("ldap:promote-group", "syncloud", "-y")
	return err
}

func (i *Installer) initialize() error {
	if err := i.prepareStorage(); err != nil {
		return err
	}
	storageDir, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}

	if err := i.database.Execute("postgres", fmt.Sprintf("ALTER USER %s WITH PASSWORD '%s';", DbUser, DbPassword)); err != nil {
		return err
	}
	if err := i.database.Execute("postgres", fmt.Sprintf("CREATE DATABASE nextcloud OWNER %s TEMPLATE template0 ENCODING 'UTF8';", DbUser)); err != nil {
		return err
	}
	if err := i.database.Execute("postgres", fmt.Sprintf("GRANT CREATE ON SCHEMA public TO %s;", DbUser)); err != nil {
		return err
	}

	realStorage, err := filepath.EvalSymlinks(storageDir)
	if err != nil {
		realStorage = storageDir
	}
	installUser := "installer-" + uuid.New().String()
	installPass := uuid.New().String()
	if _, err := i.occ.Run(
		"maintenance:install",
		"--database", "pgsql",
		"--database-host", fmt.Sprintf("%s:%d", i.database.DatabaseDir(), PsqlPort),
		"--database-name", "nextcloud",
		"--database-user", DbUser,
		"--database-pass", DbPassword,
		"--admin-user", installUser,
		"--admin-pass", installPass,
		"--data-dir", realStorage,
	); err != nil {
		return err
	}

	if _, err := i.occ.Run("app:enable", "user_ldap"); err != nil {
		return err
	}
	if _, err := i.occ.Run("ldap:create-empty-config"); err != nil {
		return err
	}

	ldapSets := [][]string{
		{"ldapHost", "ldap://localhost"},
		{"ldapPort", "389"},
		{"ldapAgentName", "cn=admin,dc=syncloud,dc=org"},
		{"ldapBase", "dc=syncloud,dc=org"},
		{"ldapAgentPassword", "syncloud"},
		{"hasMemberOfFilterSupport", "0"},
		{"ldapLoginFilter", "(&(|(objectclass=inetOrgPerson))(cn=%uid))"},
		{"ldapUserFilter", "(|(objectclass=inetOrgPerson))"},
		{"ldapUserFilterObjectclass", "inetOrgPerson"},
		{"ldapBaseUsers", "ou=users,dc=syncloud,dc=org"},
		{"ldapUserDisplayName", "cn"},
		{"ldapExpertUsernameAttr", "cn"},
		{"ldapGroupFilterObjectclass", "posixGroup"},
		{"ldapGroupDisplayName", "cn"},
		{"ldapBaseGroups", "ou=groups,dc=syncloud,dc=org"},
		{"ldapGroupFilter", "(&(|(objectclass=posixGroup)))"},
		{"ldapGroupMemberAssocAttr", "memberUid"},
		{"ldapTLS", "0"},
		{"turnOffCertCheck", "1"},
		{"ldapConfigurationActive", "1"},
	}
	for _, kv := range ldapSets {
		if _, err := i.occ.Run("ldap:set-config", "s01", kv[0], kv[1]); err != nil {
			return err
		}
	}

	if _, err := i.occ.Run("db:convert-filecache-bigint"); err != nil {
		return err
	}

	if err := i.cron.Run(); err != nil {
		return err
	}

	if _, err := i.occ.Run("group:list"); err != nil {
		return err
	}
	if _, err := i.occ.Run("user:delete", installUser); err != nil {
		return err
	}
	if _, err := i.occ.Run("db:add-missing-indices"); err != nil {
		return err
	}
	_, err = i.occ.Run("ldap:promote-group", "syncloud", "-y")
	return err
}

func (i *Installer) prepareStorage() error {
	storageDir, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}
	ncdata := path.Join(storageDir, ".ncdata")
	if f, err := os.OpenFile(ncdata, os.O_CREATE|os.O_WRONLY, 0644); err != nil {
		return err
	} else {
		f.Close()
	}
	if err := chownFile(ncdata, UserName); err != nil {
		return err
	}
	if err := os.Chmod(storageDir, 0777); err != nil {
		return err
	}
	tmpDir := path.Join(storageDir, "tmp")
	if err := os.MkdirAll(tmpDir, 0755); err != nil {
		return err
	}
	if err := linux.Chown(tmpDir, UserName); err != nil {
		return err
	}
	realStorage, err := filepath.EvalSymlinks(storageDir)
	if err != nil {
		realStorage = storageDir
	}
	return i.fixDataDirectory(realStorage)
}

func (i *Installer) fixDataDirectory(dir string) error {
	content, err := os.ReadFile(i.ncConfigFile)
	if err != nil {
		return err
	}
	pattern := regexp.MustCompile(`'datadirectory'\s*=>\s*'.*?'`)
	updated := pattern.ReplaceAllString(string(content), fmt.Sprintf("'datadirectory' => '%s'", dir))
	if err := os.WriteFile(i.ncConfigFile, []byte(updated), 0644); err != nil {
		return err
	}
	return i.fixConfigPermission()
}

func (i *Installer) migrateNextcloudConfig() error {
	if _, err := os.Stat(i.ncConfigFile); err == nil {
		return nil
	}
	old := path.Join(i.commonDir, "nextcloud", "config", "config.php")
	if _, err := os.Stat(old); err != nil {
		return nil
	}
	if err := copyFile(old, i.ncConfigFile); err != nil {
		return err
	}
	return i.fixConfigPermission()
}

func (i *Installer) fixVersionSpecificDbHost() error {
	content, err := os.ReadFile(i.ncConfigFile)
	if err != nil {
		return err
	}
	pattern := regexp.MustCompile(`'dbhost'\s*=>\s*'.*?'`)
	updated := pattern.ReplaceAllString(string(content), fmt.Sprintf("'dbhost' => '%s'", i.database.DatabaseHost()))
	if err := os.WriteFile(i.ncConfigFile, []byte(updated), 0644); err != nil {
		return err
	}
	return i.fixConfigPermission()
}

func (i *Installer) fixConfigPermission() error {
	return chownFile(i.ncConfigFile, UserName)
}

func chownFile(path, username string) error {
	cmd := exec.Command("chown", fmt.Sprintf("%s:%s", username, username), path)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("chown %s: %w: %s", path, err, string(out))
	}
	return nil
}

func (i *Installer) fixPermissions() error {
	if err := linux.Chown(i.commonDir, UserName); err != nil {
		return err
	}
	return linux.Chown(i.dataDir, UserName)
}

package installer

import (
	"fmt"
	"path"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const (
	App      = "nextcloud"
	UserName = "nextcloud"
)

type Installer struct {
	appDir         string
	commonDir      string
	dataDir        string
	configDir      string
	installFile    string
	platformClient *platform.Client
	executor       *Executor
	logger         *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	configDir := path.Join(dataDir, "config")
	return &Installer{
		appDir:         appDir,
		commonDir:      commonDir,
		dataDir:        dataDir,
		configDir:      configDir,
		installFile:    path.Join(dataDir, "installed"),
		platformClient: platform.New(),
		executor:       NewExecutor(logger),
		logger:         logger,
	}
}

func (i *Installer) Install() error {
	i.logger.Info("install")
	return i.legacy("install")
}

func (i *Installer) Configure() error {
	i.logger.Info("configure")
	return i.legacy("configure")
}

func (i *Installer) PreRefresh() error {
	i.logger.Info("pre-refresh")
	return i.legacy("pre-refresh")
}

func (i *Installer) PostRefresh() error {
	i.logger.Info("post-refresh")
	return i.legacy("post-refresh")
}

func (i *Installer) StorageChange() error {
	return i.legacyShim("storage-change")
}

func (i *Installer) AccessChange() error {
	return i.legacyShim("access-change")
}

func (i *Installer) BackupPreStop() error {
	return i.legacyShim("backup-pre-stop")
}

func (i *Installer) RestorePreStart() error {
	return i.legacyShim("restore-pre-start")
}

func (i *Installer) RestorePostStart() error {
	return i.legacyShim("restore-post-start")
}

func (i *Installer) legacy(hook string) error {
	out, err := i.executor.Run(path.Join(i.appDir, "meta/hooks-py", hook))
	i.logger.Info(out)
	return err
}

func (i *Installer) legacyShim(name string) error {
	out, err := i.executor.Run(path.Join(i.appDir, "hooks-py", name))
	i.logger.Info(out)
	return err
}

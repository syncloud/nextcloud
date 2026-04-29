package installer

import (
	"path"

	"go.uber.org/zap"
)

type OCConsole struct {
	runner   string
	executor *Executor
	logger   *zap.Logger
}

func NewOCConsole(appDir string, executor *Executor, logger *zap.Logger) *OCConsole {
	return &OCConsole{
		runner:   path.Join(appDir, "bin/occ-runner"),
		executor: executor,
		logger:   logger,
	}
}

func (o *OCConsole) Run(args ...string) (string, error) {
	o.logger.Info("occ", zap.Strings("args", args))
	out, err := o.executor.Run(o.runner, args...)
	if err != nil {
		o.logger.Error("occ failed", zap.Error(err), zap.String("output", out))
	}
	return out, err
}

type OCConfig struct {
	tool     string
	executor *Executor
	logger   *zap.Logger
}

func NewOCConfig(appDir string, executor *Executor, logger *zap.Logger) *OCConfig {
	return &OCConfig{
		tool:     path.Join(appDir, "bin/nextcloud-config"),
		executor: executor,
		logger:   logger,
	}
}

func (c *OCConfig) SetValue(key, value string) error {
	c.logger.Info("nextcloud-config", zap.String("key", key), zap.String("value", value))
	out, err := c.executor.Run(c.tool, key, value)
	if err != nil {
		c.logger.Error("config error", zap.Error(err), zap.String("output", out))
	}
	return err
}

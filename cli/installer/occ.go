package installer

import (
	"path"
	"strconv"

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
	occ    *OCConsole
	logger *zap.Logger
}

func NewOCConfig(occ *OCConsole, logger *zap.Logger) *OCConfig {
	return &OCConfig{
		occ:    occ,
		logger: logger,
	}
}

func (c *OCConfig) SetValue(key string, values ...string) error {
	c.logger.Info("config", zap.String("key", key), zap.Strings("values", values))
	if len(values) == 1 {
		args := []string{"config:system:set", key, "--value=" + values[0]}
		if values[0] == "true" || values[0] == "false" {
			args = append(args, "--type=boolean")
		}
		_, err := c.occ.Run(args...)
		return err
	}
	if _, err := c.occ.Run("config:system:delete", key); err != nil {
		c.logger.Info("could not clear key before writing it", zap.String("key", key), zap.Error(err))
	}
	for index, value := range values {
		if _, err := c.occ.Run("config:system:set", key, strconv.Itoa(index), "--value="+value); err != nil {
			return err
		}
	}
	return nil
}

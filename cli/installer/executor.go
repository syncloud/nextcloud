package installer

import (
	"fmt"
	"os/exec"
	"strings"
	"time"

	"go.uber.org/zap"
)

type Executor struct {
	logger *zap.Logger
}

func NewExecutor(logger *zap.Logger) *Executor {
	return &Executor{
		logger: logger,
	}
}

func (e *Executor) Run(app string, args ...string) (string, error) {
	cmd := exec.Command(app, args...)
	e.logger.Info("executing", zap.String("cmd", cmd.String()))
	start := time.Now()
	out, err := cmd.CombinedOutput()
	took := time.Since(start)
	for _, line := range strings.Split(string(out), "\n") {
		e.logger.Debug(line)
	}
	if err != nil {
		e.logger.Error("executed", zap.String("cmd", cmd.String()), zap.Duration("took", took), zap.Error(err))
		return string(out), fmt.Errorf("%s %v: %w: %s", app, args, err, string(out))
	}
	e.logger.Info("executed", zap.String("cmd", cmd.String()), zap.Duration("took", took))
	return string(out), nil
}

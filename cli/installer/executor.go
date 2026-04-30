package installer

import (
	"fmt"
	"os/exec"
	"strings"

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
	e.logger.Debug("executing", zap.String("cmd", cmd.String()))
	out, err := cmd.CombinedOutput()
	for _, line := range strings.Split(string(out), "\n") {
		e.logger.Debug(line)
	}
	if err != nil {
		return string(out), fmt.Errorf("%s %v: %w: %s", app, args, err, string(out))
	}
	return string(out), nil
}

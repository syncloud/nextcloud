package installer

import (
	"fmt"
	"os/exec"
	"strings"

	"go.uber.org/zap"
)

type Cron struct {
	user     string
	command  string
	executor *Executor
	logger   *zap.Logger
}

func NewCron(user string, executor *Executor, logger *zap.Logger) *Cron {
	return &Cron{
		user:     user,
		command:  fmt.Sprintf("/usr/bin/snap run %s.cron", App),
		executor: executor,
		logger:   logger,
	}
}

func (c *Cron) Remove() error {
	c.logger.Info("removing crontab task")
	out, err := exec.Command("crontab", "-u", c.user, "-l").CombinedOutput()
	if err != nil {
		// no crontab yet for this user is not an error
		return nil
	}
	var kept []string
	for _, line := range strings.Split(string(out), "\n") {
		if !strings.Contains(line, c.command) {
			kept = append(kept, line)
		}
	}
	return c.write(strings.Join(kept, "\n"))
}

func (c *Cron) Create() error {
	c.logger.Info("creating crontab task")
	existing := ""
	out, err := exec.Command("crontab", "-u", c.user, "-l").CombinedOutput()
	if err == nil {
		existing = strings.TrimRight(string(out), "\n")
	}
	entry := fmt.Sprintf("*/15 * * * * %s", c.command)
	if existing == "" {
		return c.write(entry + "\n")
	}
	return c.write(existing + "\n" + entry + "\n")
}

func (c *Cron) Run() error {
	c.logger.Info("running cron", zap.String("cmd", c.command))
	_, err := c.executor.Run("/usr/bin/snap", "run", App+".cron")
	return err
}

func (c *Cron) write(content string) error {
	cmd := exec.Command("crontab", "-u", c.user, "-")
	cmd.Stdin = strings.NewReader(content)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("crontab write failed: %w: %s", err, string(out))
	}
	return nil
}

package main

import (
	"context"
	"fmt"
	"hooks/installer"
	"hooks/log"
	"hooks/repair"
	"os"
	"os/signal"
	"syscall"
	"time"

	"go.uber.org/zap"
)

func main() {
	logger := log.HookLogger("nextcloud-repair-service", zap.DebugLevel)

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer cancel()

	srv := repair.NewServer(logger)

	go func() {
		inst := installer.New(logger)

		waitDone := srv.StartStep("wait-for-configure")
		err := inst.WaitForConfigureDone(30 * time.Minute)
		waitDone(err)
		if err != nil {
			logger.Error("aborting; configure-done marker never appeared", zap.Error(err))
			srv.MarkDone()
			return
		}
		srv.MarkConfigureDone()

		if !inst.NextcloudInstalled() {
			logger.Info("nextcloud not installed yet, skipping repair")
			srv.MarkDone()
			return
		}

		type step struct {
			name string
			fn   func() error
		}
		var steps []step
		ldapDeferred := inst.NeedsDbUpgrade()
		if inst.RefreshNeeded() || ldapDeferred {
			logger.Info("running post-refresh repair", zap.Bool("ldapDeferred", ldapDeferred))
			steps = []step{
				{"occ-upgrade", inst.RunOccUpgrade},
				{"maintenance-mode-off", inst.RunMaintenanceModeOff},
			}
			if ldapDeferred {
				steps = append(steps,
					step{"ldap-set-email-attribute", inst.RunLdapSetEmailAttribute},
					step{"group-list", inst.RunGroupList},
					step{"ldap-promote-syncloud", inst.RunLdapPromoteSyncloud},
				)
			}
			steps = append(steps,
				step{"db-add-missing-indices", inst.RunDbAddMissingIndices},
				step{"db-add-missing-columns", inst.RunDbAddMissingColumns},
				step{"db-add-missing-primary-keys", inst.RunDbAddMissingPrimaryKeys},
				step{"maintenance-repair", inst.RunMaintenanceRepair},
			)
		} else {
			logger.Info("refresh-needed marker absent; skipping heavy post-refresh repair")
		}

		failed := false
		for _, s := range steps {
			done := srv.StartStep(s.name)
			err := s.fn()
			done(err)
			if err != nil {
				failed = true
			}
		}
		if !failed {
			if err := inst.ClearRefreshNeeded(); err != nil {
				logger.Error("failed to clear refresh-needed marker", zap.Error(err))
			}
		}
		srv.MarkDone()
		logger.Info("repair work complete; status server staying alive for queries")
	}()

	if err := srv.Serve(ctx, repair.SocketPath); err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}

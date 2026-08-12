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
		ldapDeferred := inst.LdapDeferred()
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

		if len(steps) > 0 {
			attempt := inst.IncrementRepairAttempts()
			logger.Info("repair attempt", zap.Int("attempt", attempt), zap.Int("max", installer.MaxRepairAttempts))
			if attempt > installer.MaxRepairAttempts {
				logger.Error("giving up after repeated repair attempts; showing upgrade-failed page")
				if err := inst.ShowUpgradeFailedPage(); err != nil {
					logger.Error("cannot show upgrade-failed page", zap.Error(err))
				}
				srv.MarkDone()
				return
			}
			if err := inst.ShowUpgradingPage(); err != nil {
				logger.Error("cannot show upgrading page", zap.Error(err))
			}
		}

		failed := false
		coreConsistent := true
		for _, s := range steps {
			done := srv.StartStep(s.name)
			err := s.fn()
			done(err)
			if err != nil {
				failed = true
				if s.name == "occ-upgrade" {
					coreConsistent = false
				}
			}
		}
		if len(steps) > 0 {
			if coreConsistent {
				done := srv.StartStep("maintenance-mode-off-final")
				err := inst.RunMaintenanceModeOff()
				done(err)
				if err != nil {
					failed = true
				}
			} else {
				logger.Error("core upgrade failed; leaving maintenance mode on rather than exposing a half-upgraded instance")
			}
			if apps := inst.DisabledApps(); len(apps) > 0 {
				logger.Info("apps disabled to let the upgrade through", zap.Strings("apps", apps))
				srv.SetDisabledApps(apps)
			}
		}
		if len(steps) > 0 {
			if failed {
				logger.Error("repair finished with errors; showing upgrade-failed page")
				if err := inst.ShowUpgradeFailedPage(); err != nil {
					logger.Error("cannot show upgrade-failed page", zap.Error(err))
				}
			} else {
				if err := inst.ClearStatusPage(); err != nil {
					logger.Error("cannot clear status page", zap.Error(err))
				}
				if err := inst.ClearRepairAttempts(); err != nil {
					logger.Error("cannot clear repair attempts", zap.Error(err))
				}
				if err := inst.ClearLdapDeferred(); err != nil {
					logger.Error("cannot clear ldap-deferred marker", zap.Error(err))
				}
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

package main

import (
	"fmt"
	"hooks/installer"
	"os"

	"github.com/spf13/cobra"
	"github.com/syncloud/golib/log"
)

func main() {
	logger := log.Logger()

	var cmd = &cobra.Command{
		Use:          "cli",
		SilenceUsage: true,
	}

	cmd.AddCommand(&cobra.Command{
		Use: "storage-change",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("storage-change")
			return installer.New(logger).StorageChange()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use: "access-change",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("access-change")
			return installer.New(logger).AccessChange()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use: "backup-pre-stop",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("backup-pre-stop")
			return installer.New(logger).BackupPreStop()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use: "restore-pre-start",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("restore-pre-start")
			return installer.New(logger).RestorePreStart()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use: "restore-post-start",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("restore-post-start")
			return installer.New(logger).RestorePostStart()
		},
	})

	err := cmd.Execute()
	if err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}

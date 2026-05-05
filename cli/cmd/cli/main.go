package main

import (
	"context"
	"fmt"
	"hooks/installer"
	"hooks/log"
	"hooks/repair"
	"io"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/spf13/cobra"
	"go.uber.org/zap"
)

func main() {
	logger := log.Logger(zap.DebugLevel)

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

	cmd.AddCommand(&cobra.Command{
		Use: "repair-status",
		RunE: func(cmd *cobra.Command, args []string) error {
			c := &http.Client{
				Transport: &http.Transport{
					DialContext: func(ctx context.Context, _ string, _ string) (net.Conn, error) {
						var d net.Dialer
						return d.DialContext(ctx, "unix", repair.SocketPath)
					},
				},
				Timeout: 5 * time.Second,
			}
			resp, err := c.Get("http://repair/status")
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			body, err := io.ReadAll(resp.Body)
			if err != nil {
				return err
			}
			fmt.Println(string(body))
			return nil
		},
	})

	err := cmd.Execute()
	if err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}

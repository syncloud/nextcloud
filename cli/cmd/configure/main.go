package main

import (
	"fmt"
	"hooks/installer"
	"hooks/log"
	"os"

	"github.com/spf13/cobra"
	"go.uber.org/zap"
)

func main() {
	logger := log.HookLogger("nextcloud-configure", zap.DebugLevel)

	var rootCmd = &cobra.Command{
		Use:          "configure",
		SilenceUsage: true,
		RunE: func(cmd *cobra.Command, args []string) error {
			return installer.New(logger).Configure()
		},
	}

	err := rootCmd.Execute()
	if err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}

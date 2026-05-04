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
	logger := log.HookLogger("nextcloud-install", zap.DebugLevel)

	var rootCmd = &cobra.Command{
		Use:          "install",
		SilenceUsage: true,
		RunE: func(cmd *cobra.Command, args []string) error {
			return installer.New(logger).Install()
		},
	}

	err := rootCmd.Execute()
	if err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}

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

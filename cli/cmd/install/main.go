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

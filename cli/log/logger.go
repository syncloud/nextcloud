package log

import (
	"fmt"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func Logger(level zapcore.Level) *zap.Logger {
	logConfig := zap.NewProductionConfig()
	logConfig.Encoding = "console"
	logConfig.EncoderConfig.TimeKey = ""
	logConfig.EncoderConfig.ConsoleSeparator = " "
	logConfig.Level = zap.NewAtomicLevelAt(level)
	logger, err := logConfig.Build()
	if err != nil {
		panic(fmt.Sprintf("can't initialize zap logger: %v", err))
	}
	return logger
}

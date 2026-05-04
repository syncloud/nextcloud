package log

import (
	"fmt"
	"log/syslog"
	"os"

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

func HookLogger(tag string, level zapcore.Level) *zap.Logger {
	encConfig := zap.NewProductionEncoderConfig()
	encConfig.TimeKey = ""
	encConfig.ConsoleSeparator = " "
	encoder := zapcore.NewConsoleEncoder(encConfig)
	atom := zap.NewAtomicLevelAt(level)

	cores := []zapcore.Core{
		zapcore.NewCore(encoder, zapcore.Lock(os.Stdout), atom),
	}
	if w, err := syslog.New(syslog.LOG_INFO|syslog.LOG_DAEMON, tag); err == nil {
		cores = append(cores, zapcore.NewCore(encoder, zapcore.AddSync(w), atom))
	}
	return zap.New(zapcore.NewTee(cores...))
}

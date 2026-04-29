package installer

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path"
	"strconv"

	"go.uber.org/zap"
)

type Database struct {
	appDir          string
	dataDir         string
	configDir       string
	user            string
	databaseDir     string
	port            int
	backupFile      string
	majorVersionDst string
	majorVersionSrc string
	executor        *Executor
	logger          *zap.Logger
}

func NewDatabase(appDir, dataDir, configDir, user string, port int, executor *Executor, logger *zap.Logger) *Database {
	return &Database{
		appDir:          appDir,
		dataDir:         dataDir,
		configDir:       configDir,
		user:            user,
		databaseDir:     path.Join(dataDir, "database"),
		port:            port,
		backupFile:      path.Join(dataDir, "database.dump"),
		majorVersionDst: path.Join(dataDir, "db.major.version"),
		majorVersionSrc: path.Join(appDir, "db.major.version"),
		executor:        executor,
		logger:          logger,
	}
}

func (d *Database) DatabaseDir() string {
	return d.databaseDir
}

func (d *Database) DatabaseHost() string {
	return fmt.Sprintf("%s:%d", d.databaseDir, d.port)
}

func (d *Database) Execute(database, sql string) error {
	_, err := d.executor.Run(
		"snap", "run", App+".psql",
		"-U", d.user,
		"-d", database,
		"-c", sql,
	)
	return err
}

func (d *Database) Init() error {
	_, err := d.executor.Run(path.Join(d.appDir, "bin/initdb.sh"), d.databaseDir)
	return err
}

func (d *Database) InitConfig() error {
	src := path.Join(d.configDir, "postgresql.conf")
	dst := path.Join(d.databaseDir, "postgresql.conf")
	return copyFile(src, dst)
}

func (d *Database) Remove() error {
	if _, err := os.Stat(d.backupFile); errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("backup file does not exist: %s", d.backupFile)
	}
	if _, err := os.Stat(d.databaseDir); err == nil {
		return os.RemoveAll(d.databaseDir)
	}
	return nil
}

func (d *Database) Restore() error {
	_, err := d.executor.Run("snap", "run", App+".psql", "-f", d.backupFile, "postgres")
	return err
}

func (d *Database) Backup() error {
	if _, err := d.executor.Run("snap", "run", App+".pgdumpall", "-f", d.backupFile); err != nil {
		return err
	}
	return copyFile(d.majorVersionSrc, d.majorVersionDst)
}

func (d *Database) Port() int {
	return d.port
}

func (d *Database) PortString() string {
	return strconv.Itoa(d.port)
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

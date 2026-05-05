package repair

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"os"
	"sync"
	"time"

	"go.uber.org/zap"
)

const SocketPath = "/var/snap/nextcloud/current/repair.sock"

type Step struct {
	Name       string    `json:"name"`
	StartedAt  time.Time `json:"started_at"`
	DurationMs int64     `json:"duration_ms"`
	Error      string    `json:"error,omitempty"`
}

type Status struct {
	StartedAt     time.Time `json:"started_at"`
	ConfigureDone bool      `json:"configure_done"`
	Steps         []Step    `json:"steps"`
	Done          bool      `json:"done"`
}

type Server struct {
	mu     sync.RWMutex
	status Status
	logger *zap.Logger
}

func NewServer(logger *zap.Logger) *Server {
	return &Server{
		status: Status{StartedAt: time.Now().UTC(), Steps: []Step{}},
		logger: logger,
	}
}

func (s *Server) MarkConfigureDone() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.status.ConfigureDone = true
}

func (s *Server) StartStep(name string) func(error) {
	s.mu.Lock()
	idx := len(s.status.Steps)
	start := time.Now().UTC()
	s.status.Steps = append(s.status.Steps, Step{Name: name, StartedAt: start})
	s.mu.Unlock()
	s.logger.Info("step start", zap.String("name", name))
	return func(err error) {
		took := time.Since(start)
		s.mu.Lock()
		s.status.Steps[idx].DurationMs = took.Milliseconds()
		if err != nil {
			s.status.Steps[idx].Error = err.Error()
		}
		s.mu.Unlock()
		if err != nil {
			s.logger.Error("step end", zap.String("name", name), zap.Duration("took", took), zap.Error(err))
		} else {
			s.logger.Info("step end", zap.String("name", name), zap.Duration("took", took))
		}
	}
}

func (s *Server) MarkDone() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.status.Done = true
}

func (s *Server) Snapshot() Status {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := s.status
	out.Steps = append([]Step(nil), s.status.Steps...)
	return out
}

func (s *Server) Serve(ctx context.Context, socket string) error {
	if err := os.Remove(socket); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	l, err := net.Listen("unix", socket)
	if err != nil {
		return err
	}
	if err := os.Chmod(socket, 0666); err != nil {
		s.logger.Warn("chmod socket failed", zap.Error(err))
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(s.Snapshot())
	})
	srv := &http.Server{Handler: mux}
	go func() {
		<-ctx.Done()
		_ = srv.Close()
	}()
	s.logger.Info("repair status server listening", zap.String("socket", socket))
	if err := srv.Serve(l); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}

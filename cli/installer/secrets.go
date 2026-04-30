package installer

import (
	"bufio"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"os"
	"strings"
)

type SignalingSecrets struct {
	SessionHashkey string
	SessionBlockkey string
	InternalSecret string
	BackendSecret  string
}

func generateHexSecret() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

func loadOrCreateSignalingSecrets(path string) (*SignalingSecrets, error) {
	if _, err := os.Stat(path); errors.Is(err, os.ErrNotExist) {
		return createSignalingSecrets(path)
	}

	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	values := map[string]string{}
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		if i := strings.Index(line, "="); i > 0 {
			values[line[:i]] = line[i+1:]
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return &SignalingSecrets{
		SessionHashkey: values["signaling_session_hashkey"],
		SessionBlockkey: values["signaling_session_blockkey"],
		InternalSecret: values["signaling_internal_secret"],
		BackendSecret:  values["signaling_backend_secret"],
	}, nil
}

func createSignalingSecrets(path string) (*SignalingSecrets, error) {
	hashkey, err := generateHexSecret()
	if err != nil {
		return nil, err
	}
	blockkey, err := generateHexSecret()
	if err != nil {
		return nil, err
	}
	internal, err := generateHexSecret()
	if err != nil {
		return nil, err
	}
	backend, err := generateHexSecret()
	if err != nil {
		return nil, err
	}

	content := strings.Join([]string{
		"signaling_session_hashkey=" + hashkey,
		"signaling_session_blockkey=" + blockkey,
		"signaling_internal_secret=" + internal,
		"signaling_backend_secret=" + backend,
	}, "\n") + "\n"

	if err := os.WriteFile(path, []byte(content), 0600); err != nil {
		return nil, err
	}

	return &SignalingSecrets{
		SessionHashkey: hashkey,
		SessionBlockkey: blockkey,
		InternalSecret: internal,
		BackendSecret:  backend,
	}, nil
}
